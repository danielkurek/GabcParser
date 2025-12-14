from lark import Lark
from typing import Literal
from pathlib import Path

def load_parser(variation: Literal['gabc', 'mei-gabc', 's-gabc'], **kwargs) -> Lark:
    supported_types = ['gabc', 'mei-gabc', 's-gabc']
    
    if not isinstance(variation, str):
        raise TypeError("`variation` should be of type str")
    if variation not in supported_types:
        raise ValueError(f"Invalid value of `variation`. Supported types {', '.join('\'' + x + '\'' for x in supported_types)}")
    
    parser = Lark.open(str(Path("grammar") / f"{variation}.lark"), **kwargs)
    return parser
