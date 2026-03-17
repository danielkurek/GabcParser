from GabcParser import load_parser
from lark import Lark, visitors, Tree, Token

def pitch_to_num(pitch) -> int:
    return pitch[1]*7 + ((ord(pitch[0]) - ord('c')) % 7)

class PitchConvertor(visitors.Transformer):
    def __init__(self, debug: bool = False):
        self.current_clef = None
        self.current_clef_num = None
        self.current_clef_position = None
        self.debug = debug
    
    def clef(self, children):
        assert len(children) == 2
        assert children[0].data == "clef_symbol"
        assert children[1].data == "clef_number"
        clef_symbol = children[0]
        clef_number= children[1]

        assert len(clef_symbol.children) == 1
        assert len(clef_number.children) == 1
        symbol = clef_symbol.children[0].value
        number = int(clef_number.children[0].value)
        self.current_clef = (symbol, number)
        self.current_clef_num = pitch_to_num((symbol.lower(), 3))
        self.current_clef_position = 1 + 2*number
        return Tree(data="clef", children=children)
    
    def pitch(self, children):
        assert self.current_clef_num is not None and self.current_clef_position is not None
        assert len(children) == 2
        pitch = children[0].value, int(children[1].value)
        pitch_num = pitch_to_num(pitch)
        pitch_distance = pitch_num - self.current_clef_num
        pitch_position = self.current_clef_position + pitch_distance
        assert pitch_position >= 0 and pitch_position <= 12
        gabc_pitch = chr(ord('a') + pitch_position)
        if self.debug:
            print(f"{pitch=} -> {gabc_pitch} {self.current_clef=} {self.current_clef_num=} {self.current_clef_position=}")
        return Tree(data="pitch", children=[Token("PITCH", gabc_pitch)])

if __name__ == "__main__":
    gabc_parser = load_parser("mei-gabc")

    with open("examples/einsiedeln2.txt") as f:
        parsed_tree = gabc_parser.parse(f.read())
        transformed = PitchConvertor().transform(parsed_tree)
        tokens = transformed.scan_values(lambda v: isinstance(v, Token))
        f.seek(0)
        print(f.read())
        print("".join(t.value for t in tokens))
