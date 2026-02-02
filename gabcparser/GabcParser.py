from lark import Lark
from typing import Literal
import importlib.resources
from . import grammars

def load_parser(variation: Literal['gabc', 'mei-gabc', 's-gabc'], **kwargs) -> Lark:
    if not isinstance(variation, str):
        raise TypeError("`variation` should be of type str")
    if variation not in grammars.supported_grammars:
        raise ValueError(f"Invalid value of `variation`. Supported types {', '.join(f'`{x}`' for x in grammars.supported_grammars)}")
    grammar_path = importlib.resources.files(__name__.split(".", maxsplit=1)[0]) / "grammars" / f"{variation}.lark"
    with grammar_path.open("r", encoding="utf-8") as f:
        parser = Lark(f, **kwargs)
        return parser

load_parser('gabc')