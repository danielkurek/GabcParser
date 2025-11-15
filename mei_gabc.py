from lark import Lark, visitors

def pitch_to_num(pitch):
    return pitch[1]*7 + ((ord(pitch[0]) - ord('c')) % 7)

class PitchConvertor(visitors.Interpreter):
    def __init__(self):
        self.current_clef = None
        self.current_clef_num = None
        self.current_clef_position = None
    
    def clef(self, tree):
        assert len(tree.children) == 2
        assert tree.children[0].data == "clef_symbol"
        assert tree.children[1].data == "clef_number"
        clef_symbol = tree.children[0]
        clef_number= tree.children[1]

        assert len(clef_symbol.children) == 1
        assert len(clef_number.children) == 1
        symbol = clef_symbol.children[0].value
        number = int(clef_number.children[0].value)
        self.current_clef = (symbol, number)
        self.current_clef_num = pitch_to_num((symbol.lower(), 3))
        self.current_clef_position = 1 + 2*number
    
    def syllable(self, tree):
        self.visit_children(tree)
    
    def syl_musical_symbols(self, tree):
        self.visit_children(tree)
    
    def musical_symbol(self, tree):
        self.visit_children(tree)
    
    def pitch(self, tree):
        assert len(tree.children) == 2
        pitch = tree.children[0].value, int(tree.children[1].value)
        pitch_num = pitch_to_num(pitch)
        pitch_distance = pitch_num - self.current_clef_num
        pitch_position = self.current_clef_position + pitch_distance
        assert pitch_position >= 0 and pitch_position <= 12
        print(f"{pitch=} -> {chr(ord('a') + pitch_position)} {self.current_clef=} {self.current_clef_num=} {self.current_clef_position=}")
    
    def custos(self, tree):
        self.visit_children(tree)

gabc_parser = Lark.open("grammar/mei-gabc.lark", debug=True)

with open("examples/einsiedeln2.txt") as f:
    parsed_tree = gabc_parser.parse(f.read())
    # print(parsed_tree.pretty())
    PitchConvertor().visit(parsed_tree)