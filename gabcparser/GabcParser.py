from lark import Lark
from typing import Literal
from pathlib import Path
from . import grammars

def load_parser(variation: Literal['gabc', 'mei-gabc', 's-gabc'], **kwargs) -> Lark:
    if not isinstance(variation, str):
        raise TypeError("`variation` should be of type str")
    if variation not in grammars.supported_grammars:
        raise ValueError(f"Invalid value of `variation`. Supported types {', '.join(f'\'{x}\'' for x in grammars.supported_grammars)}")
    
    parser = Lark.open(str(Path("grammar") / f"{variation}.lark"), **kwargs)
    return parser
