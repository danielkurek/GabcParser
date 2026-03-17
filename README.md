# GABC parsers

This project is used to convert between different GABC formats used in [AMNLT](https://huggingface.co/datasets/PRAIG/AMNLT) dataset.

## Installation

1. Clone this repository
   ```bash
   git clone https://github.com/danielkurek/GabcParser.git
   ```
2. Navigate into the cloned repository
   ```bash
   cd
   ```
3. Install the package
   ```bash
   pip install .
   ```
   - use `pip install -e .` if you plan to modify the source code (otherwise you would need to reinstall the package after every change)

## Grammars

The grammars follow a consistent structure at the beginning of the parse tree in order to simplify further processing:

- Depth 0: `start`
- Depth 1: `syllable`
- Depth 2: `syl_lyric_symbols` or `syl_musical_symbols`

However, there is an exception in `mei-gabc` grammar. Depth 1 may also contain the `malformed_ending` non-terminal (only as the last non-terminal at this level). To maintain the same structure as `syllable` non-terminal, it differentiates between lyrical and musical non-terminals at the depth 2. In this case we have only descendent of `malformed_ending` and that is `malformed_ending_music`. The consistent structure is helpful in post processing because we typically have different processing for lyrical and musical symbols. We can make this differentiation at a fixed depth, i.e at the depth 2.

The following sections describe each of the implemented grammars in details. Checkout [comparison table](comparison_table.md) for brief overview.

### GABC (with music tags)

GABC format that is used in [GregoSynth dataset](https://huggingface.co/datasets/PRAIG/GregoSynth_staffLevel) (from AMNLT paper). It is normal GABC format with one difference, music tag `<m>` is added to every music symbol.

There is no single formal definition of the GABC format. The grammar was created using [Gregorio (version 6.1.0) reference documentation](https://github.com/gregorio-project/gregorio/releases/tag/v6.1.0) and the corresponding NABC reference (although NABC is not parsed). The created grammar was validated using [GregoSynth dataset](https://huggingface.co/datasets/PRAIG/GregoSynth_staffLevel) from AMNLT paper. There are still some samples that do not conform to the grammar. However, majority of these samples include either errors (which led to incorrect render) or NABC notation (which is currently not supported). The following table summarizes the unconforming samples.

| Error                                     | # samples | Notes                                                               |
|-------------------------------------------|-----------|---------------------------------------------------------------------|
| Incorrect parentheses pairing             | 1596      | Either `))` (1439 occurrences) or `<m>(` (260 occurrences)          |
| NABC notation                             | 965       | Occurrence of `<m>|`                                                |
| `<tag>` modifiers within music part       | 101       | Mainly due to incorrect music part separation (could be corrected)  |
| `{` and `}` within music part             | 96        | Unknown use (something stylistic)                                   |
| `v` or `V` as a prefix                    | 67        | Should be a suffix instead                                          |
| Choral sign `[cs:...]`                    | 55        | Not implemented                                                     |
| `[alt:...]` above line text within notes  | 45        | Not implemented                                                     |
| Custom ledger line without note           | 24        | Incorrect syntax (some caused by `!` as suffix)                     |
| Braces within music (mainly `[ocba:...]`) | 10        | Not implemented                                                     |
| Macros                                    | 5         | Samples do not contain macro definitions                            |
| `@[...]` note fusing group                | 2         | Not implemented                                                     |
| Episema position tuning without episema   | 2         | Incorrect syntax                                                    |
| Other                                     | 205       | Not yet analyzed                                                    |
| **Total**                                 | **3162**  | Some samples have more than one issue (counted twice in this table) |

- supported features (music tags are omitted for better readability)
  - lyrics
    - normal text
    - lyric tags - `<sp>`, `<b>`, `<i>`, `<c>`, `<ul>`, `<sc>`, `<v>`, `<tt>`, `<nlba>`, `<e>`, `<alt>`, `<eu>`
      - tags support recursive use - with the exception of `<sp>`, `<v>` and `<eu>`
      - TeX support might be limited
    - syllable centering - `{text}`
  - music - enclosed with parentheses and each music symbol has `<m>` as a prefix
    - clef - `c` and `f` type and position number
      - flat clef
      - linked clefs - using `@`
    - notes
      - pitches - a-m
        - rhombus shape - capitalized with optional variation number (0-2)
      - prefixes
        - initio debilis - `-`
        - stem removal - `@`
      - repetition
        - di/tristropha - `ss`/`sss`
        - bi/trivirga - `vv`/`vvv`
      - suffixes
        - stems - virga left/right - `V`/`v`
        - shape
          - oriscus
            - scapus - `O` (with optional `0`/`1`) or `0`
            - normal - `o` (with optional `0`/`1`)
          - quilisma - `w`/`W`
          - strophicus - `s`
          - liquescent
            - normal - `~`
            - descending - `>`
            - ascending - `<`
          - quadratum - `q`
        - accidentals
          - flat/neutral/sharp - `x`/`y`/`#`
            - parenthesized accidentals - suffix `!`
          - soft flat/neutral/sharp - `X`/`Y`/`##`
        - rhythmic sign
          - punctum mora - `.` with optional `0`/`1`
          - vertical episema - `'` with optional `0`/`1`
          - horizontal episema - `_` with optional `0`-`5`/horizontal episema tuning (section 6.4.21 in Gregorio reference)
        - empty note - `r0`
        - note accents - `R` or `r1`-`r8`
        - pitch custos - `+`
        - custom ledger line - section 6.4.18 in Gregorio reference
    - custos - `z0` - custos according to the following note
    - separation bar
      - virgula - `` ` `` with optional `0`
      - divisio minimis - `^` with optional `0`
      - divisio minima - `,` with optional position `0`-`6`
      - divisio minor - `;` with optional position `1`-`6`
      - divisio maior - `:` with optional `?` for dotted line
      - divisio finalis - `::`
      - moddifiers - suffix to any of the above separation bars
        - vertical episema - `'`
        - bar brace - `_`
    - neume spacing
      - large separation - ` `
      - zero width space - `!`
      - half space - `/0`
      - small separation - `/` with optional `!`
      - medium separation - `//`
      - scaled large separation - `/[factor]` where `factor` is positive or negative decimal number
    - line break - `z` or `Z` with optional `+`/`-`
    - no custos - `[nocustos]`
- known unsupported features
  - `<nlba>` tags within notes
  - macros
  - choral signs
  - braces
  - shape hints
  - stem length
  - simple slurs
  - above line text within notes
  - verbatim TeX within notes
  - note fusing groups `@[...]`

### Systematic GABC (S-GABC)

Systematic GABC notation was proposed by [Thomae et. al](https://doi.org/10.1145/3660570.3660581). Although, the paper includes EBNF grammar, it is not complete and there are some minor mistakes. This work implements the grammar on best effort basis using the original paper and the [AMNLT Solesmes dataset](https://huggingface.co/datasets/PRAIG/Solesmes_staffLevel) as reference.

The grammar was validated using the [Solesmes dataset](https://huggingface.co/datasets/PRAIG/Solesmes_staffLevel). There are still some samples that do not conform to the created grammar (0.82% error rate), summarized in the following table.

| Error                                               | # samples | Notes                                                     |
|-----------------------------------------------------|-----------|-----------------------------------------------------------|
| Wrong placement of separation bar                   | 1         | Separation bar (usually `;`) between pitch and its suffix |
| Neumatic cut as a suffix (instead of a prefix)      | 1         | Incorrect syntax                                          | 
| Virga as a prefix (instead of a suffix)             | 1         | Incorrect syntax                                          |
| Mistyped separation bar (`1;` instead of `;1`)      | 1         | Incorrect syntax                                          |
| Custos syntax wrong ordering (`+i` instead of `i+`) | 1         | Incorrect syntax                                          |
| Unknown music notation - `h>7V`                     | 1         | Unknown meaning                                           |
| Unknown music notation - `ViV>`                     | 1         | Unknown meaning (probably typo)                           |
| **Total**                                           | **7**     |                                                           |

All errors are caused by the dataset not conforming to the S-GABC grammar which can be easily corrected for the small number of samples. This indicates that there wasn't a strict grammar checking during dataset creation.


- shortcomings of the official grammar
  - no grammar rule for lyric text
  - no enforcement pairing of text modifiers
  - missing non-terminal definition - `attachment` in `gr.14`
  - missing oblique shape (porrectus) definition
  - missing separation bar definitions
  - missing uncertain reading definition

- differences to the official grammar
  - minor syntactic reformating of rules
  - added support for lyric text
  - parsing malformed music contained in Solesmes dataset - examples
    - `1` at the beginning of music part
    - `!` or `/` at the end of music part
    - new line inside music part
    - unknown characters - `|`, `»`, `"`, `”`, `“`
  - `/` as a prefix to clef - e.g. used when clef is changed within single music part
  - added separation bar definition - same as GABC (without suffix modifiers)
  - added GABC style custos
  - added `CONT` inside music part (with added music tags)
  - note prefixes
    - note can have more than one prefix
    - removed attachment from note - since there is no definition for it
    - added porrectus prefix (oblique shape) - `°`
    - unknown prefixes - `*`, `w`, `"`, `”`, `“`
    - multiple versions of exclamation mark are accepted (also `¡`)
  - implemented completely illegible readings - empty parentheses
  - allow neumatic cut to be in format `/1`-`/6` (without square brackets) - used in Solesmes dataset
  - added uncertain readings - `r` with optional `1`-`7`

### Pseudo GABC

Pseudo GABC was created in AMNLT paper as a conversion from MEI to a format similar to GABC. It differs from GABC significantly in pitch notation, an absolute pitch is used instead of position within staff lines.

There is no official documentation for this format, everything was reverse engineered from the [Einsiedeln](https://huggingface.co/datasets/PRAIG/Einsiedeln_staffLevel) and [Salzinnes](https://huggingface.co/datasets/PRAIG/Salzinnes_staffLevel) datasets. The grammar was validated using the datasets. Currently, the grammar parses all of the samples in both datasets. However, it was achieved by also parsing malformed samples, e.g. missing closing parentheses, ...

- supported features
  - lyrics - plain text without formatting
  - music - enclosed in parentheses, symbols are separated by a single space character
    - notes
      - prefix - with space separation
        - accidental - `f` or `n`
      - pitch - `a`-`h` + octave `0`-`9`, e.g. `d3`
      - suffixes
        - virga left/right - `-n`/`-s`
        - porrectus - `-l` for every note in porrectus (should be only two notes)
        - shape
          - rhombus - `-se`
          - two tails up/down - `-a`/`-c`
            - holds only in Einsiedeln dataset, Salzinnes has these suffixes but there is no consistent visual indicator
      - malformed note - `s`+pitch, e.g. `sf2`
    - clef - e.g. `C3`
      - type - `C` or `F`
      - position - `1`-`5` or negative numbers (`-1`-`-5`)
    - separation bar - either part of lyrics or music, `|`
    - custos - `z-`+pitch, e.g. `z-d3`
      - malformed custos - `g-`+pitch, e.g. `g-d3`
    - malformed music - opening parenthesis repeated after one note
      - only present in single sample
    - malformed ending - missing closing parenthesis
