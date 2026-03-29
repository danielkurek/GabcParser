from typing import override
from lark import Lark, Token, ParseTree, Transformer, Tree, Discard
from lark import exceptions as lark_exceptions
import csv
import argparse
from pathlib import Path
from .. import grammars
from .. import GabcParser
from datasets import load_dataset

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Seperate lyrical and musical symbols in GABC files")
    parser.add_argument("-s", "--skip", type=int, default=1, help="Skip first n lines of the csv input file (default is 1 -> skip header)")
    parser.add_argument("-t", "--threads", type=int, default=None, help="Process file in multiple threads")
    parser.add_argument("-o", "--output_dir", type=str, default="out/", help="Output directory")
    parser.add_argument("--transcript_column", type=str, default="transcription", help="Transcription column name")
    parser.add_argument("grammar", choices=grammars.supported_grammars, help="GABC grammar variation")
    parser.add_argument("dataset", help="Huggingface dataset name")


class MeiGabcToCommon(Transformer):
    """
    Lark Transformer to convert `mei-gabc` parse tree to common encoding.

    The focus is on resulting string constructed from the non-terminals. 
    The structure of resulting parse tree might differ to the one produced by `common-gabc` grammar.
    """
    _MUSIC_TAG = Token("MUSIC_TAG", "<m>")
    
    def __init__(self, debug: bool = False):
        super().__init__()
        self.current_clef = None
        self.current_clef_num = None
        self.current_clef_position = None
    
    @staticmethod
    def pitch_to_num(pitch) -> int:
        return pitch[1]*7 + ((ord(pitch[0]) - ord('c')) % 7)
    
    @override
    def __default__(self, data, children, meta):
        if len(children) == 0:
            return Discard
        return Tree(data, children, meta)
    
    def syl_musical_symbols(self, children):
        # add parentheses to symbols that do not have them
        if len(children) == 1 and isinstance(children[0], Tree) and (children[0].data == "separation_bar" or children[0].data == "custos"):
            return Tree("syl_musical_symbols", [
                    Token("PARENTH_OPEN", "("),
                    children[0],
                    Token("PARENTH_CLOSE", ")"),
                ])
        return Tree("syl_musical_symbols", children)

    def syl_musical_symbols_parentheses(self, children):
        # convert porrectus
        def note_index_porrectus(children):
            for i,child in enumerate(children):
                if isinstance(child, Tree) and child.data == "suffix" \
                    and any(isinstance(x, Tree) and x.data == "porrectus" for x in child.children):
                    return i
            return None
        prev_porrectus_note = None
        # find notes and store the direct preceding note with porrectus
        for i in range(len(children)):
            # take into account only non-terminals (Tree), musical symbols are separated with spaces which are terminals (Tokens)
            if isinstance(children[i], Tree) and children[i].data == "musical_symbol":
                music_symbol = children[i]
                note = None
                for child in music_symbol.children:
                    if isinstance(child, Tree) and child.data == "note":
                        note = child
                        break
                if note is not None:
                    porrectus_index = note_index_porrectus(note.children)
                    if porrectus_index is None:
                        prev_porrectus_note = None
                    else:
                        # remove `-l` suffix
                        note.children.pop(porrectus_index)
                        if prev_porrectus_note is None:
                            prev_porrectus_note = note
                        else:
                            # convert to porrectus
                            prev_porrectus_note.children.insert(0, Tree("prefix", [
                                Tree("porrectus", [Token("DEGREE", "°")])
                                ]))
                            prev_porrectus_note = None
                            pass
                elif prev_porrectus_note is not None:
                    # not a direct sibling
                    prev_porrectus_note = None
            elif isinstance(children[i], Tree):
                # should not happen
                prev_porrectus_note = None
        
        # remove spaces
        children = [x for x in children if not (isinstance(x, Token) and x.type == "SPACE")]
        return Tree("syl_musical_symbols_parentheses", children)
    
    def malformed_music_salzinnes(self, children):
        # fixes type made in one sample
        assert len(children) == 4
        assert isinstance(children[1], Tree) and children[1].data == "note"
        assert isinstance(children[3], Tree) and children[3].data == "syl_musical_symbols_parentheses"
        note = children[1]
        syl_musical_parentheses = children[3]

        assert isinstance(syl_musical_parentheses.children[0], Token) and syl_musical_parentheses.children[0].type == "PARENTH_OPEN"
        syl_musical_parentheses.children.insert(1, note)
        return syl_musical_parentheses

    def malformed_ending(self, children):
        return Tree("syllable", children)
    
    def malformed_ending_music(self, children):
        if len(children) == 1:
            # `malformed_custos` was already converted to `custos` since this is bottom-up
            assert isinstance(children[0], Tree) and children[0].data == "custos"
            return Tree("syl_musical_symbols_parentheses", [
                    Token("PARENTH_OPEN", "("),
                    children[0],
                    Token("PARENTH_CLOSE", ")"),
                ])
        return Tree("syl_musical_symbols", [
                Tree("syl_musical_symbols_parentheses", children + [Token("PARENTH_CLOSE", ")")])
            ])

    def clef(self, children):
        # pitch conversion
        assert len(children) == 2
        assert children[0].data == "clef_symbol"
        assert children[1].data == "clef_number"
        clef_symbol = children[0]
        clef_number= children[1]

        # clef_symbol and clef_number are already converted -> added music tags
        assert len(clef_symbol.children) == 2
        assert len(clef_number.children) == 2 or len(clef_number.children) == 4
        symbol = clef_symbol.children[1].value
        number = int("".join(x.value for x in clef_number.children[1::2]))
        self.current_clef = (symbol, number)
        self.current_clef_num = self.pitch_to_num((symbol.lower(), 3))
        self.current_clef_position = 1 + 2*number

        return Tree("clef", children)
    
    def clef_symbol(self, children):
        assert len(children) == 1
        return Tree("clef_symbol", [self._MUSIC_TAG, *children])
    
    def clef_number(self, children):
        if len(children) == 1:
            return Tree("clef_number", [self._MUSIC_TAG, children[0]])
        elif len(children) == 2:
            return Tree("clef_number", [self._MUSIC_TAG, children[0], self._MUSIC_TAG, children[1]])
        raise RuntimeError("clef_number should have length 1 or 2")

    def note(self, children):
        # convert pitch to rhombus if necessary
        pitch = None
        rhombus = None
        for i,child in enumerate(children):
            if not isinstance(child, Tree):
                continue
            if child.data == "pitch":
                assert pitch is None
                pitch = child
            if child.data == "suffix":
                suffix = child
                for x in suffix.children:
                    if isinstance(x, Tree) and x.data == "shape" and x.children[0].data == "rhombus":
                        assert rhombus is None
                        rhombus = i
                        break
        if rhombus is not None:
            children.pop(rhombus)
        if pitch is not None:
            # pitch is already converted to GABC notation
            assert len(pitch.children) == 1 and isinstance(pitch.children[0], Token)
            pitch_sym = pitch.children[0].value
            rhombus = rhombus is not None
            pitch.children = [
                Tree(
                    "rhombus_pitch" if rhombus else "square_pitch",
                    [
                        self._MUSIC_TAG,
                        Token(pitch.children[0].type, pitch_sym.upper() if rhombus else pitch_sym)
                    ])
            ]
        
        # remove spaces
        children = [x for x in children if not (isinstance(x, Token) and x.type == "SPACE")]

        return Tree("note", children)

    def flat(self, children):
        return Tree("flat", [self._MUSIC_TAG, Token("CHAR_X", "x")])
        
    def neutral(self, children):
        return Tree("neutral", [self._MUSIC_TAG, Token("CHAR_Y", "y")])

    def malformed_note(self, children):
        # remove typo
        return Tree("note", children[1:])
    
    def pitch(self, children):
        assert self.current_clef_num is not None and self.current_clef_position is not None
        assert len(children) == 2
        pitch = children[0].value, int(children[1].value)
        pitch_num = self.pitch_to_num(pitch)
        pitch_distance = pitch_num - self.current_clef_num
        pitch_position = self.current_clef_position + pitch_distance
        assert pitch_position >= 0 and pitch_position <= 12
        gabc_pitch = chr(ord('a') + pitch_position)
        
        # MUSIC_TAG is added in `note` function
        return Tree("pitch", [Token("PITCH", gabc_pitch)])
    
    def suffix(self, children):
        if len(children) == 0:
            return Discard
        if isinstance(children[0], Token) and children[0].type == "MINUS":
            children = children[1:]
        return Tree("suffix", children)
    
    def virga_right(self, children):
        return Tree("virga_right", [self._MUSIC_TAG, Token("CHAR_V", "v")])
    
    def virga_left(self, children):
        return Tree("virga_left", [self._MUSIC_TAG, Token("CHAR_V_", "V")])
    
    def liquescent_two_tails_down(self, children):
        return Tree("liquescent_two_tails_down", [self._MUSIC_TAG, Token("CHAR_GT", ">")])

    def liquescent_two_tails_up(self, children):
        return Tree("liquescent_two_tails_up", [self._MUSIC_TAG, Token("CHAR_LT", "<")])
    
    def custos(self, children):
        pitch = None
        for child in children:
            if isinstance(child, Tree) and child.data == "pitch":
                pitch = child
                break
        assert pitch is not None
        return Tree("custos", [pitch, self._MUSIC_TAG, Token("CHAR_PLUS", "+")])
    
    def malformed_custos(self, children):
        return self.custos(children)
    
    def separation_bar(self, children):
        return Tree("separation_bar", [
            Tree("bar_maior", [self._MUSIC_TAG, Token("COLON", ":")])
            ])


def main(args: argparse.Namespace):
    gabc_parser = GabcParser.load_parser(args.grammar)
    dataset = load_dataset(args.dataset)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    convertor = MeiGabcToCommon()
    for split in dataset.keys():
        parsed = gabc_parser.parse(dataset[split][args.transcript_column][5])
        transformed = convertor.transform(parsed)
        tokens = transformed.scan_values(lambda v: isinstance(v, Token))
        print("".join(token.value for token in tokens))


        
if __name__ == "__main__":
    args = parser.parse_args()
    main(args)