from lark import Lark, Token
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
    parser.add_argument("--include_music_tag", default=False, action="store_true", help="Include music tag in music split")
    parser.add_argument("-o", "--output_dir", type=str, default="out/", help="Output directory")
    parser.add_argument("grammar", choices=grammars.supported_grammars, help="GABC grammar variation")
    parser.add_argument("csv_input", help="CSV input file to validate (expected format: ID,TEXT)")


# nodes whose whole subtree is music / lyrics (lyric nodes cannot contain music in any grammar)
# -> the tree is traversed only until one of these nodes is found
_MUSIC_NODES = ("syl_musical_symbols", "malformed_ending_music")
_LYRIC_NODES = ("syl_lyric_symbols",)

def _iter_parts(tree):
    """Yield `(is_music, part)` in the order of the text; `part` is a music/lyric node or a token outside of them (e.g. `<nlba>` tag)."""
    for child in tree.children:
        if isinstance(child, Token):
            yield False, child
        elif child.data in _MUSIC_NODES:
            yield True, child
        elif child.data in _LYRIC_NODES:
            yield False, child
        else:
            yield from _iter_parts(child)

def _tokens(part):
    return [part] if isinstance(part, Token) else part.scan_values(lambda v: isinstance(v, Token))

def separate_lyrics_music(text: str, parser: Lark, include_music_tag=False, filtered_symbol=None):
    """
    `text`: text compatible with grammar of `parser`
    `parser`: Lark parser
    `include_music_tag`: include MUSIC_TAG (default: `<m>`) in the music split
    `filtered_symbol`: replace filtered parts with a symbol `filtered_symbol` - e.g. can be used to insert space between lyric/music parts separated with the other part (music/lyric)
      - each run of consecutive filtered parts is replaced by one symbol
    """
    try:
        tree = parser.parse(text)
    except lark_exceptions.UnexpectedInput:
        return None, None
    lyrics, music = [], []
    previous_is_music = None
    for is_music, part in _iter_parts(tree):
        if filtered_symbol is not None and is_music != previous_is_music:
            # start of a run -> replaced by one symbol in the other split
            if is_music:
                lyrics.append(filtered_symbol)
            else:
                music.append(filtered_symbol)
        previous_is_music = is_music
        if is_music:
            music.extend(token.value for token in _tokens(part) if include_music_tag or token.type != "MUSIC_TAG")
        else:
            lyrics.extend(token.value for token in _tokens(part))
    return "".join(lyrics), "".join(music)

def csv_reader(file, skip_lines):
    with open(file) as f:
        reader = csv.reader(f, delimiter=",")
        skip = skip_lines
        for row in reader:
            if skip > 0:
                skip -= 1
                continue
            yield row

def worker_init(grammar_file_path, include_music_tag, filtered_symbol):
    global lark_parser
    global _filtered_symbol
    global _include_music_tag
    _filtered_symbol = filtered_symbol
    _include_music_tag = include_music_tag
    lark_parser = GabcParser.load_parser(grammar_file_path)

def process_row(row):
    global lark_parser
    global _filtered_symbol
    global _include_music_tag
    return row[0], separate_lyrics_music(row[1], lark_parser, _include_music_tag, _filtered_symbol)

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
            lyrics, music = separate_lyrics_music(row[1], gabc_parser, args.include_music_tag, args.filtered_symbol)
            lyric_writer.writerow((row[0], lyrics))
            music_writer.writerow((row[0], music))

    else:
        pool = Pool(args.threads, initializer=worker_init, initargs=(args.grammar, args.include_music_tag, args.filtered_symbol))
        total_lines = None
        with open(args.csv_input, "rb") as f:
            total_lines = sum(1 for _ in f)
        for id,(lyrics,music) in tqdm.tqdm(pool.imap(process_row, csv_reader(args.csv_input, args.skip), 20), total=total_lines):
            lyric_writer.writerow((id, lyrics))
            music_writer.writerow((id, music))

        
if __name__ == "__main__":
    args = parser.parse_args()
    main(args)