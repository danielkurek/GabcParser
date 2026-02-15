from lark import Lark, Token, ParseTree
from lark import exceptions as lark_exceptions
import csv
import argparse
from multiprocessing import Pool
import tqdm
from pathlib import Path
from .. import grammars
from .. import GabcParser

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Seperate lyrical and musical symbols in GABC files")
    parser.add_argument("-s", "--skip", type=int, default=1, help="Skip first n lines of the csv input file (default is 1 -> skip header)")
    parser.add_argument("-t", "--threads", type=int, default=None, help="Process file in multiple threads")
    parser.add_argument("--filtered_symbol", type=str, default=None, help="Filter symbol that will be in place of filtered out parts")
    parser.add_argument("-o", "--output_dir", type=str, default="out/", help="Output directory")
    parser.add_argument("grammar", choices=grammars.supported_grammars, help="GABC grammar variation")
    parser.add_argument("csv_input", help="CSV input file to validate (expected format: ID,TEXT)")


def filter_syllables(tree, pred, filtered_symbol=None):
    for syl in tree.children:
        assert syl.data in ["syllable", "malformed_syllable"]
        assert len(syl.children) == 1
        assert syl.children[0].data in ["syl_lyric_symbols", "syl_musical_symbols", "malformed_music"]
        if pred(syl.children[0]):
            yield syl
        elif filtered_symbol is not None:
            yield Token("filtered_symbol", filtered_symbol)

def separate_lyrics_music(text: str, parser: Lark, include_music_tag=False, filtered_symbol=None):
    """
    `text`: text compatible with grammar of `parser`
    `parser`: Lark parser
    `include_music_tag`: include MUSIC_TAG (default: `<m>`) in the music split
    `filtered_symbol`: replace filtered parts with a symbol `filtered_symbol` - e.g. can be used to insert space between lyric/music parts separated with the other part (music/lyric)
    """
    try:
        tree = parser.parse(text)
    except lark_exceptions.UnexpectedCharacters:
        return None, None
    lyric_symbols = filter_syllables(tree, lambda x: x.data == "syl_lyric_symbols", filtered_symbol)
    music_symbols = filter_syllables(tree, lambda x: x.data == "syl_musical_symbols" or x.data == "malformed_music", filtered_symbol)
    lyric_tree = ParseTree("start", list(lyric_symbols))
    music_tree = ParseTree("start", list(music_symbols))

    lyric_tokens = lyric_tree.scan_values(lambda v: isinstance(v, Token))
    music_tokens = music_tree.scan_values(lambda v: isinstance(v, Token) and (include_music_tag or v.type != "MUSIC_TAG"))
    lyrics = "".join(token.value for token in lyric_tokens)
    music = "".join(token.value for token in music_tokens)
    return lyrics, music

def csv_reader(file, skip_lines):
    with open(file) as f:
        reader = csv.reader(f, delimiter=",")
        skip = skip_lines
        for row in reader:
            if skip > 0:
                skip -= 1
                continue
            yield row

def worker_init(grammar_file_path, filtered_symbol):
    global lark_parser
    global _filtered_symbol
    _filtered_symbol = filtered_symbol
    lark_parser = GabcParser.load_parser(grammar_file_path)

def process_row(row):
    global lark_parser
    global _filtered_symbol
    return row[0], separate_lyrics_music(row[1], lark_parser, filtered_symbol=_filtered_symbol)

def main(args: argparse.Namespace):
    gabc_parser = GabcParser.load_parser(args.grammar)
    csv_input = Path(args.csv_input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    lyric_file = open(output_dir / f"{csv_input.stem}_lyric.csv", "w")
    music_file = open(output_dir / f"{csv_input.stem}_music.csv", "w")
    lyric_writer = csv.writer(lyric_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
    music_writer = csv.writer(music_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
    if args.threads is None:
        for row in csv_reader(args.csv_input, args.skip):
            lyrics, music = separate_lyrics_music(row[1], gabc_parser, filtered_symbol=args.filtered_symbol)
            lyric_writer.writerow((row[0], lyrics))
            music_writer.writerow((row[0], music))

    else:
        pool = Pool(args.threads, initializer=worker_init, initargs=(args.grammar,args.filtered_symbol))
        total_lines = None
        with open(args.csv_input, "rb") as f:
            total_lines = sum(1 for _ in f)
        for id,(lyrics,music) in tqdm.tqdm(pool.imap(process_row, csv_reader(args.csv_input, args.skip), 20), total=total_lines):
            lyric_writer.writerow((id, lyrics))
            music_writer.writerow((id, music))

        
if __name__ == "__main__":
    args = parser.parse_args()
    main(args)