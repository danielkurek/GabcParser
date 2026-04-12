from typing import override
from lark import Lark, Token, ParseTree, Transformer, Tree, Discard
from lark import exceptions as lark_exceptions
import csv
import argparse
from pathlib import Path
from .. import grammars
from .. import GabcParser
from datasets import load_dataset
from functools import partial
from collections import namedtuple

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Seperate lyrical and musical symbols in GABC files")
    parser.add_argument("-t", "--threads", type=int, default=None, help="Process file in multiple threads")
    parser.add_argument("-o", "--output_dir", type=str, default="out/", help="Output directory")
    parser.add_argument("--transcript_column", type=str, default="transcription", help="Transcription column name")
    parser.add_argument("--remove_failed_rows", default=False, action="store_true", help="Remove rows which failed the conversion")
    parser.add_argument("--remove_mislabeled_custos", default=False, action="store_true", help="Remove mislabeled custos (with wrong pitch). Only applies to `mei-gabc` grammar")
    parser.add_argument("grammar", choices=grammars.supported_grammars, help="GABC grammar variation")
    parser.add_argument("dataset", help="Huggingface dataset name")

class GabcToCommon(Transformer):
    _MUSIC_TAG = Token("MUSIC_TAG", "<m>")

    def __init__(self):
        super().__init__()
        self.PorrectusHistoryItem = namedtuple("PorrectusHistoryItem", ["note", "pitch_num", "allowed_positions"])
        self.porrectus_threshold = 5 # MAX_AMBITUS constant in Gregorio source code

    @override
    def __default__(self, data, children, meta):
        if len(children) == 0:
            return Discard
        return Tree(data, children, meta)

    # def syl_lyric_symbols(self, children):
    #     # TODO: change modified lyrics to this rule
    #     pass

    def special_lyric(self, children):
        text = "".join([x.value for x in children if isinstance(x, Token) and x.type == "SYLLABLE"])
        new_text = None
        # TODO: maybe add more cases
        match text:
            case "ae":
                new_text = "æ"
            case "oe":
                new_text = "œ"
            case "A/":
                new_text = "Ⱥ"
            case "R/":
                new_text = "Ꞧ"
            case "V/":
                new_text = "Ꝟ"
            case "'ae":
                new_text = "æ'"
            case "'oe":
                new_text = "œ'"
            case _:
                new_text = text
        return Tree("syl_lyric_symbols", [Token("SYLLABLE", new_text)])

    def bold_text(self, children):
        return Tree("syl_lyric_symbols", [x for x in children if isinstance(x, Tree)])

    def italic_text(self, children):
        return Tree("syl_lyric_symbols", [x for x in children if isinstance(x, Tree)])

    def color_text(self, children):
        return Tree("syl_lyric_symbols", [x for x in children if isinstance(x, Tree)])

    def underline_text(self, children):
        return Tree("syl_lyric_symbols", [x for x in children if isinstance(x, Tree)])

    def small_caps_text(self, children):
        return Tree("syl_lyric_symbols", [x for x in children if isinstance(x, Tree)])

    def teletype_text(self, children):
        return Tree("syl_lyric_symbols", [x for x in children if isinstance(x, Tree)])

    def nlba_text(self, children):
        return Tree("syl_lyric_symbols", [x for x in children if isinstance(x, Tree)])

    def elision_text(self, children):
        return Tree("syl_lyric_symbols", [x for x in children if isinstance(x, Tree)])

    def above_line_text(self, children):
        return Tree("syl_lyric_symbols", [x for x in children if isinstance(x, Tree)])

    def euouae_text(self, children):
        return Tree("syl_lyric_symbols", [x for x in children if isinstance(x, Tree)])

    def tex_text(self, children):
        # no TeX command are allowed
        return Discard

    def syllable_centering(self, children):
        return Tree("syl_lyric_symbols", [x for x in children if isinstance(x, Token) and x.type == "SYLLABLE"])
    
    def syl_musical_symbols(self, children):
        assert isinstance(children[0], Token) and children[0].type == "PARENTH_OPEN"
        assert isinstance(children[-1], Token) and children[-1].type == "PARENTH_CLOSE"
        # remove multiple zero_width_space in succession - keep only one
        # unwrap notes if needed
        # TODO: detect porrectus
        if len(children) == 2:
            # remove empty parentheses
            return Discard
        note_history = []
        i = 1
        while i < len(children)-1:
            if not isinstance(children[i], Tree):
                # this should not happen
                i += 1
                note_history.clear()
                continue
            assert children[i].data == "musical_symbol"
            musical_symbol = children[i]
            assert len(musical_symbol.children) == 1 and isinstance(musical_symbol.children[0], Tree)
            if musical_symbol.children[0].data == "zero_width_space" \
                 and isinstance(children[i-1], Tree) and children[i-1].children[0].data =="zero_width_space":
                children.pop(i)
                note_history.clear()
                # do not increment i; next element is at i-th position
                continue
            if musical_symbol.children[0].data == "note_unwrap":
                note_unwrap = musical_symbol.children[0]
                # remove this symbol and insert its children
                children.pop(i)
                for offset,child in enumerate(note_unwrap.children):
                    children.insert(i+offset, Tree("musical_symbol", [child]))
                i += len(note_unwrap.children) # any of the notes in note_unwrap cannot be part of porrectus nor is it zero-width space
                note_history.clear()
                continue
            if musical_symbol.children[0].data == "note":
                # Detection of porrectus
                # rules according to Gregorio source code and experimentation (probably not 100% correct)
                #   - porrectus determination - add_note_to_a_glyph in src/gabc/gabc-glyphs-determination.c
                #   - grammar that determines note shape - src/gabc/gabc-notes-determination.l
                # - 3 notes in succession - the second note must be lower than first and third note must be higher than second
                #   - the `lower` and `higher` must be within 5 pitches from the previous note
                # - notes shape must be S_PUNCTUM in order to form porrectus
                # - shape - only square shaped notes
                # - disallowed prefixes - `-` <- triggers closing of current glyph
                # - prefix `@` can be only on first or last note (because of closing glyph)
                # - allowed suffixes - custom ledger line, punctum mora, horizontal/vertical episema, `r1`-`r8`, `r`
                # - allowed suffixes only at the last note: liquescent(_two_tails_[up|down])
                # - disallowed suffixes - accidental, `R`, `r0`, repetition, quadratum, oriscus, quilisma, virga, strophicus
                note = musical_symbol.children[0]
                pitch = None
                can_be_second = True
                allowed_positions = [True, True, True]
                possible_porrectus = True
                for child in note.children:
                    if not isinstance(child, Tree):
                        continue
                    if child.data == "pitch":
                        assert len(child.children) == 1 and isinstance(child.children[0], Tree)
                        pitch_child = child.children[0]
                        assert len(pitch_child.children) >= 2 and isinstance(pitch_child.children[1], Token)
                        pitch = pitch_child.children[1].value
                    if child.data == "repetition":
                        raise RuntimeError("Unexpected repetition found - there should be none at this point in the program")
                    if child.data == "prefix":
                        prefix = child
                        assert len(prefix.children) == 0 and isinstance(prefix.children[0], Tree)
                        prefix_type = prefix.children[0].data
                        if prefix_type == "initio_debilis":
                            possible_porrectus = False
                            break
                        elif prefix_type == "remove_stem":
                            allowed_positions[1] = False
                        else:
                            raise RuntimeError(f"Unexpected prefix type '{prefix_type}'")
                    if child.data == "suffix":
                        suffix = child
                        assert len(suffix.children) == 1 and isinstance(suffix.children[0], Tree)
                        suffix_type = suffix.children[0].data
                        if suffix_type not in ["custom_ledger_line", "note_accents", "empty_note", "rhythmic_sign", "shape"]:
                            possible_porrectus = False
                            break
                        if suffix_type == "shape":
                            shape = suffix.children[0]
                            assert len(shape.children) == 1 and isinstance(shape.children[0], Tree)
                            shape_type = shape.children[0].data
                            if shape_type not in ["liquescent", "liquescent_two_tails_down", "liquescent_two_tails_up"]:
                                possible_porrectus = False
                                break
                            allowed_positions[0] = False
                            allowed_positions[1] = False
                if not possible_porrectus:
                    note_history.clear()
                    i += 1
                    continue
                if pitch is None:
                    raise ValueError("Note does not contain any pitch - critical error")
                if pitch.isupper():
                    note_history.clear()
                    i += 1
                    continue
                if len(pitch) != 1 or ord(pitch) < ord('a') or ord(pitch) > ord('m'):
                    raise ValueError("Unexpected pitch value")
                pitch_num = ord(pitch) - ord('a')
                note_history.append(self.PorrectusHistoryItem(note, pitch_num, allowed_positions))
                if len(note_history) == 3:
                    correct_positions = all(x.allowed_positions[pos] for pos,x in enumerate(note_history))
                    rel_pitch_2 = note_history[1].pitch_num - note_history[0].pitch_num
                    rel_pitch_3 = note_history[2].pitch_num - note_history[1].pitch_num
                    correct_pitches = rel_pitch_2 < 0 and rel_pitch_2 >= -self.porrectus_threshold \
                        and rel_pitch_3 > 0 and rel_pitch_3 <= self.porrectus_threshold
                    if correct_positions and correct_pitches:
                        note_history[0].note.children.insert(0, Tree("prefix", [
                            Tree("porrectus", [Token("DEGREE", "°")])
                        ]))
                    else:
                        note_history.pop(0)
                elif len(note_history) > 3:
                    raise RuntimeError("Unexpected note_history length")
            i += 1
        if len(children) == 0:
            return Discard
        return Tree("syl_musical_symbols", children)

    def linked_clef(self, children):
        assert len(children) == 3 and isinstance(children[2], Tree) and children[2].data == "clef"
        return Tree("clef", children[2].children)
    
    def note(self, children):
        # convert repetitions to several notes
        repetition_index = None
        pitch = None
        for i in range(len(children)):
            if not isinstance(children[i], Tree):
                continue
            if children[i].data == "pitch":
                pitch = children[i]
            if children[i].data == "repetition":
                repetition_index = i
                break
        if repetition_index is None:
            return Tree("note", children)
        
        repetition = children.pop(repetition_index)
        assert len(repetition.children) == 1 and isinstance(repetition.children[0], Tree)
        assert pitch is not None
        repetition = repetition.children[0]
        repetition_num = 1

        if repetition.data.startswith("di") or repetition.data.startswith("bi"):
            repetition_num = 2
        elif repetition.data.startswith("tri"):
            repetition_num = 3
        else:
            ValueError(f"Unknown repetition type `{repetition.data}`")
        
        notes = []
        prefixes = [x for x in children if isinstance(x, Tree) and x.data == "prefix"]
        pitch_token = pitch.children[0].children[1]
        assert isinstance(pitch_token, Token)
        if repetition.data.endswith("stropha"):
            new_pitch = Tree("pitch", [Tree("rhombus_pitch", [self._MUSIC_TAG, Token("CHAR_A2M_", pitch_token.value.upper())])])
            suffix = Tree("shape", [Tree("liquescent_two_tails_down", [self._MUSIC_TAG, Token("CHAR_GT", ">")])])
            notes.append(Tree("note", prefixes + [new_pitch, suffix]))
            for _ in range(1, repetition_num):
                notes.append(Tree("note",  [new_pitch, suffix]))
        elif repetition.data.endswith("virga"):
            new_pitch = Tree("pitch", [Tree("square_pitch", [self._MUSIC_TAG, Token("CHAR_A2M", pitch_token.value.lower())])])
            notes.append(Tree("note", prefixes + [new_pitch]))
            for _ in range(1, repetition_num):
                notes.append(Tree("note",  [new_pitch]))
        else:
            raise ValueError(f"Unknown repetition type `{repetition.data}`")
        # unwrapping is done in `syl_musical_symbols`
        return Tree("note_unwrap", notes)

    def di_tristropha(self, children):
        assert len(children) >= 4
        count = sum(1 for x in children if isinstance(x, Token) and x.type != "MUSIC_TAG")
        name_prefix = ""
        if count == 2:
            name_prefix = "di"
        elif count == 3:
            name_prefix = "tri"
        else:
            ValueError("Expecting 2 or 3 non music tag tokens")
        return Tree(f"{name_prefix}stropha", children)

    def bi_trivirga(self, children):
        assert len(children) >= 4
        count = sum(1 for x in children if isinstance(x, Token) and x.type != "MUSIC_TAG")
        name_prefix = ""
        if count == 2:
            name_prefix = "bi"
        elif count == 3:
            name_prefix = "tri"
        else:
            ValueError("Expecting 2 or 3 non music tag tokens")
        return Tree(f"{name_prefix}virga", children)

    def initio_debilis(self, children):
        # needed for correct porrectus detection; will not be in the output
        return Tree("initio_debilis", [])
    
    def neume_spacing(self, children):
        return Tree("zero_width_space", [self._MUSIC_TAG, Token("EXCLAM_MARK", "!")])
    
    def rhombus_pitch_shape(self, children):
        return Discard
    
    def oriscus(self, children):
        return Tree("oriscus", [self._MUSIC_TAG, Token("CHAR_O", "o")])
    
    def quadratum(self, children):
        # need this for proper porrectus detection
        return Tree("quadratum", [])
    
    def quadratum_with_lines(self, children):
        # need this for proper porrectus detection
        return Tree("quadratum", [])

    def empty_note(self, children):
        assert len(children) == 1 and isinstance(children[0], Tree)
        # the distinction is needed for porrectus detection
        name = "empty_note_with_lines" if children[0].data == "empty_note_with_lines" else "empty_note"
        return Tree(name, [self._MUSIC_TAG, Token("CHAR_R", "r")])

    def accidental_parenthesized(self, children):
        return Discard
    
    def soft_flat(self, children):
        return Tree("flat", [self._MUSIC_TAG, Token("CHAR_X", "x")])

    def soft_neutral(self, children):
        return Tree("neutral", [self._MUSIC_TAG, Token("CHAR_Y", "y")])

    def soft_sharp(self, children):
        return Tree("sharp", [self._MUSIC_TAG, Token("CHAR_HASH", "#")])
    
    def punctum_mora_position(self, children):
        return Discard
    
    def position_vertical_episema(self, children):
        return Discard
    
    # def position_horizontal_episema(self, children):
    #     return Discard
    
    def position_tuning_episema(self, children):
        return Discard
    
    def note_accent(self, children):
        # it is rendered as empty note in available data
        return Tree("empty_note", [self._MUSIC_TAG, Token("CHAR_R", "r")])
    
    def custom_ledger_line(self, children):
        return Discard
    
    def line_break_implicit_custos(self, children):
        return Tree("implicit_custos", [self._MUSIC_TAG, Token("CHAR_Z_", "Z")])
    
    def no_custos(self, children):
        return Discard
    
    def separation_bar_suffix(self, children):
        return Discard

class SGabcToCommon(Transformer):
    _MUSIC_TAG = Token("MUSIC_TAG", "<m>")
    """
    Lark Transformer to convert `s-gabc` parse tree to common encoding.

    The focus is on resulting string constructed from the non-terminals. 
    The structure of resulting parse tree might differ to the one produced by `common-gabc` grammar.
    """
    def __init__(self):
        super().__init__(visit_tokens=True)
    
    @override
    def __default__(self, data, children, meta):
        if len(children) == 0:
            return Discard
        return Tree(data, children, meta)

    def lyric_symbols(self, children):
        assert len(children) == 3
        assert isinstance(children[1], Tree) and children[1].data == "lyric"
        # `lyric` is already converted to `SYLLABLE`
        assert len(children[1].children) == 1 \
            and isinstance(children[1].children[0], Token) \
            and children[1].children[0].type == "SYLLABLE"
        return children[1].children[0]
    
    def open_text_modifiers(self, children):
        return Discard
    
    def close_text_modifiers(self, children):
        return Discard
    
    def unknown_prefix(self, children):
        return Discard
    
    def unknown_suffix(self, children):
        return Discard
    
    def illegible_reading(self, children):
        return Discard # TODO: check
    
    def malformed_music(self, children):
        if len(children) == 0:
            return Discard
        assert len(children) == 1 and isinstance(children[0], Tree)
        return Tree("syl_musical_symbols_parentheses", children[0].children)
    
    def malformed_music_missing_tag(self, children):
        # remove new line and remove multiple instances of `zero_width_space` in succession
        assert isinstance(children[0], Token) and children[0].type == "PARENTH_OPEN"
        i = 1 # we do not need to check first children
        while i < len(children):
            if isinstance(children[i], Token):
                if children[i].type == "NEW_LINE":
                    children.pop(i)
                    # do not increment i; next element is at i-th position
                    continue
            if not isinstance(children[i], Tree):
                i += 1
                continue
            # skipped first item -> the indexing cannot underflow
            if children[i].data == "zero_width_space" \
                 and isinstance(children[i-1], Tree) and children[i-1].data == "zero_width_space":
                children.pop(i)
                # do not increment i; next element is at i-th position
                continue
            i += 1
        return Tree("malformed_music_missing_tag", children)
    
    def no_space_no_tag(self, children):
        return Tree("zero_width_space", [self._MUSIC_TAG, Token("EXCLAM_MARK", "!")])
    
    def pitch_no_tag(self, children):
        return Tree("pitch", children)
    
    def square_pitch_no_tag(self, children):
        return Tree("square_pitch", [self._MUSIC_TAG, *children])

    def rhombus_pitch_no_tag(self, children):
        return Tree("rhombus_pitch", [self._MUSIC_TAG, *children])

    def uncertain_reading_no_tag(self, children):
        return Discard

    def malformed_music_unknown_seq(self, children):
        return Discard
    
    def malformed_music_new_line(self, children):
        return Discard
    
    def unknown_musical_symbol(self, children):
        return Discard
    
    def cont(self, children):
        return Discard # TODO check
    
    def note(self, children):
        # keep only one `zero_width_space`, delete the rest
        i = 0
        found_zero_width_space = False
        while i < len(children):
            if not isinstance(children[i], Tree):
                i += 1
                continue
            if children[i].data != "prefix":
                break
            prefix = children[i]
            assert len(prefix.children) == 1
            if isinstance(prefix.children[0], Tree) and prefix.children[0].data == "zero_width_space":
                if found_zero_width_space:
                    children.pop(i)
                    # do not increment i; next element is at i-th position
                    continue
                found_zero_width_space = True
            i += 1
        return Tree("note", children)
    
    def unknown_note_prefix(self, children):
        return Discard
    
    def neumatic_cut(self, children):
        return Tree("zero_width_space", [self._MUSIC_TAG, Token("EXCLAM_MARK", "!")])
    
    def no_space(self, children):
        return Tree("zero_width_space", children)
    
    def uncertain_reading(self, children):
        return Discard
    
    def oriscus(self, children):
        return Tree("oriscus", [self._MUSIC_TAG, Token("CHAR_O", "o")])
    
    def EXCLAM_MARK(self, token):
        return Token("EXCLAM_MARK", "!")
    
    def QUOTE_MARK(self, token):
        return Token("QUOTE_MARK", "\"")
    
    def DEGREE(self, token):
        return Token("DEGREE", "°")
    
    def V_LYRIC(self, token):
        return Token("SYLLABLE", "Ꝟ")

    def R_LYRIC(self, token):
        return Token("SYLLABLE", "Ꞧ")

    def A_LYRIC(self, token):
        return Token("SYLLABLE", "Ⱥ")

    def OE_LYRIC(self, token):
        return Token("SYLLABLE", "œ")

    def AE_LYRIC(self, token):
        return Token("SYLLABLE", "æ")

class MeiGabcToCommon(Transformer):
    """
    Lark Transformer to convert `mei-gabc` parse tree to common encoding.

    The focus is on resulting string constructed from the non-terminals. 
    The structure of resulting parse tree might differ to the one produced by `common-gabc` grammar.
    """
    _MUSIC_TAG = Token("MUSIC_TAG", "<m>")
    
    def __init__(self, remove_mislabeled_custos: bool = False):
        super().__init__()
        self.current_clef = None
        self.current_clef_num = None
        self.current_clef_position = None
        self.remove_mislabeled_custos = remove_mislabeled_custos
    
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
        rhombus = False
        prefix_move = None
        i = 0
        while i < len(children):
            if not isinstance(children[i], Tree):
                i += 1
                continue
            if children[i].data == "prefix_move":
                prefix_move = children[i]
                children.pop(i)
                # do not increment i; next element is at i-th position
                continue
            elif children[i].data == "pitch":
                assert pitch is None
                pitch = children[i]
                if prefix_move is not None:
                    prefix_move.data = "suffix"
                    children.insert(i+1, prefix_move)
                    i += 2 # move to next element - ignore moved prefix
                    continue
            elif children[i].data == "suffix":
                suffix = children[i]
                # minus was already removed
                assert len(suffix.children) == 1
                if isinstance(suffix.children[0], Tree) \
                      and suffix.children[0].data == "shape" \
                      and suffix.children[0].children[0].data == "rhombus":
                    # remove rhombus suffix
                    children.pop(i)
                    # do not increment i; next element is at i-th position
                    continue
            i += 1
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

    def prefix(self, children):
        assert len(children) == 2 and isinstance(children[0], Tree) and children[0].data == "accidental"
        # remove space from prefix
        return Tree("prefix_move", [children[0]])

    def accidental_doubled(self, children):
        assert len(children) == 3 and isinstance(children[0], Tree) and children[0].data in ["flat", "neutral"]
        return Tree("accidental", [children[0]])

    def flat(self, children):
        return Tree("flat", [self._MUSIC_TAG, Token("CHAR_X", "x")])
        
    def neutral(self, children):
        return Tree("neutral", [self._MUSIC_TAG, Token("CHAR_Y", "y")])

    def malformed_note(self, children):
        # remove typo and check if pitch conversion failed
        if isinstance(children[1], Tree) and children[1].data == "pitch_error":
            raise RuntimeError("Failed to convert pitch")
        return Tree("note", children[1:])
    
    def pitch(self, children):
        assert self.current_clef_num is not None and self.current_clef_position is not None
        assert len(children) == 2
        pitch = children[0].value, int(children[1].value)
        pitch_num = self.pitch_to_num(pitch)
        pitch_distance = pitch_num - self.current_clef_num
        pitch_position = self.current_clef_position + pitch_distance
        if (pitch_position < 0 or pitch_position > 12) and self.remove_mislabeled_custos:
            # if it is part of custos, whole custos will be removed
            # otherwise error will be thrown in note processing
            return Tree("pitch_error", children)
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
            if not isinstance(child, Tree):
                continue
            if child.data == "pitch":
                pitch = child
                break
            if child.data == "pitch_error":
                # this custos is most likely mislabeled
                return Discard
        assert pitch is not None
        return Tree("custos", [pitch, self._MUSIC_TAG, Token("CHAR_PLUS", "+")])
    
    def malformed_custos(self, children):
        return self.custos(children)
    
    def separation_bar(self, children):
        return Tree("separation_bar", [
            Tree("bar_maior", [self._MUSIC_TAG, Token("COLON", ":")])
            ])

def process_batch(batch, indices, grammar, transcript_column, remove_mislabeled_custos):
    parser = GabcParser.load_parser(args.grammar)
    transformer = None
    match args.grammar:
        case grammars.GABC:
            transformer = GabcToCommon()
        case grammars.S_GABC:
            transformer = SGabcToCommon()
        case grammars.MEI_GABC:
            transformer = MeiGabcToCommon(remove_mislabeled_custos)
    transformed_col = f"{transcript_column}_common"
    batch[transformed_col] = [None] * len(batch[transcript_column])
    for i in range(len(batch[transcript_column])):
        text = batch[transcript_column][i]
        try:
            parsed = parser.parse(text)
            transformed = transformer.transform(parsed)
            tokens = transformed.scan_values(lambda v: isinstance(v, Token))
            batch[transformed_col][i] = "".join(token.value for token in tokens)
        except lark_exceptions.UnexpectedCharacters:
            print(f"Could not parse sample at index {indices[i]}")
        except lark_exceptions.VisitError as err:
            print(f"Could not transform sample (index: {indices[i]}): {err.rule=} {err.orig_exc=}")
    return batch

def main(args: argparse.Namespace):
    gabc_parser = GabcParser.load_parser(args.grammar)
    dataset = load_dataset(args.dataset)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    process_fn = partial(process_batch, grammar=args.grammar, transcript_column=args.transcript_column, remove_mislabeled_custos=args.remove_mislabeled_custos)
    dataset = dataset.map(process_fn, batched=True, with_indices=True, batch_size=256, num_proc=args.threads, load_from_cache_file=False)
    if args.remove_failed_rows:
        dataset = dataset.filter(lambda x: x is not None, input_columns=f"{args.transcript_column}_common", num_proc=args.threads)
    dataset.save_to_disk(f"out/common_encoding/{args.dataset.replace("/", "-")}", num_proc=args.threads)
        
if __name__ == "__main__":
    args = parser.parse_args()
    main(args)