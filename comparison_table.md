# Comparison of the formats

| Feature                      | GABC               | S-GABC              | MEI-GABC           | Common                                                                                 |
| ---------------------------- | ------------------ | ------------------- | ------------------ | -------------------------------------------------------------------------------------- |
| **Lyrics**                   |                    |                     |                    |                                                                                        |
| - normal text                | :white_check_mark: | :white_check_mark:  | :white_check_mark: | :white_check_mark:                                                                     |
| - formatting                 | :white_check_mark: | :white_check_mark:  | :x:                | :x:                                                                                    |
| -- bold                      | :white_check_mark: | :white_check_mark:  | :x:                | :x:                                                                                    |
| -- italic                    | :white_check_mark: | :white_check_mark:  | :x:                | :x:                                                                                    |
| -- color                     | :white_check_mark: | :white_check_mark:  | :x:                | :x:                                                                                    |
| -- underline                 | :white_check_mark: | :white_check_mark:  | :x:                | :x:                                                                                    |
| -- small caps                | :white_check_mark: | :white_check_mark:  | :x:                | :x:                                                                                    |
| -- teletype                  | :white_check_mark: | :x:                 | :x:                | :x:                                                                                    |
| -- above line text           | :white_check_mark: | :x:                 | :x:                | :x:                                                                                    |
| -- arbitrary TeX             | :white_check_mark: | :x:                 | :x:                | :x:                                                                                    |
| -- syllable centering        | :white_check_mark: | :x:                 | :x:                | :x:                                                                                    |
| -- euouae tag                | :white_check_mark: | :x:                 | :x:                | :x:                                                                                    |
| -- special symbols           | :white_check_mark: | :white_check_mark:  | :x:                | :x:                                                                                    |
| **Music**                    |                    |                     |                    |                                                                                        |
| - music tag                  | :white_check_mark: | :white_check_mark:  | :x:                | :white_check_mark:                                                                     |
| - clef                       | :white_check_mark: | :white_check_mark:  | :white_check_mark: | :white_check_mark:                                                                     |
| -- flat clef                 | :white_check_mark: | :white_check_mark:  | :x:                | :white_check_mark:                                                                     |
| -- `C` and `F` clef          | :white_check_mark: | :white_check_mark:  | :white_check_mark: | :white_check_mark:                                                                     |
| -- linked clef               | :white_check_mark: | :x:                 | :x:                | TODO: check meaning                                                                    |
| - note                       | :white_check_mark: | :white_check_mark:  | :white_check_mark: | :white_check_mark:                                                                     |
| -- pitch                     | relative           | relative            | absolute           | relative                                                                               |
| -- square/rhombus shape      | :white_check_mark: | :white_check_mark:  | :white_check_mark: | :white_check_mark:                                                                     |
| -- repetition                | :white_check_mark: | :x:                 | :x:                | :x:                                                                                    |
| -- virga                     | :white_check_mark: | :white_check_mark:  | :white_check_mark: | :white_check_mark:                                                                     |
| --- left/right               | :white_check_mark: | :white_check_mark:  | :white_check_mark: | :white_check_mark:                                                                     |
| --- explicit virga           | :x:                | :white_check_mark:? | :white_check_mark: | TODO: check if doable                                                                  |
| -- empty note                | :white_check_mark: | :x:                 | :x:                | :white_check_mark:? TODO: how to deal with it                                                         |
| -- note accent               | :white_check_mark: | :x:                 | :x:                | :x: TODO: how to deal with it; only r1 is used - rendered as empty note without accent |
| -- custom ledger line        | :white_check_mark: | :x:                 | :x:                | :x:                                                                                    |
| - uncertain reading          | :x:                | :white_check_mark:  | :x:                | :x:                                                                                    |
| - custos                     | :white_check_mark: | :white_check_mark:  | :white_check_mark: | :white_check_mark:                                                                     |
| -- explicit pitch            | :white_check_mark: | :white_check_mark:  | :white_check_mark: | :white_check_mark:                                                                     |
| -- implicit pitch            | :white_check_mark: | :white_check_mark:  | :x:                | :white_check_mark:                                                                     |
| - note spacing               | :white_check_mark: | :white_check_mark:  | :x:                | :x:??                                                                                  |
| -- zero width space          | :white_check_mark: | :white_check_mark:  | :x:                | TODO                                                                                   |
| -- normal space              | :white_check_mark: | :x:                 | :x:                | TODO                                                                                   |
| -- factor space              | :white_check_mark: | :white_check_mark:  | :x:                | TODO                                                                                   |
| - note shape                 | :white_check_mark: | :white_check_mark:  | :white_check_mark: | :white_check_mark:                                                                     |
| -- strophicus                | :white_check_mark: | :white_check_mark:  | :x:                | :white_check_mark:?                                                                    |
| -- quilisma                  | :white_check_mark: | :white_check_mark:  | :x:                | :white_check_mark:?                                                                    |
| -- oriscus                   | :white_check_mark: | :white_check_mark:  | :x:                | :white_check_mark:?                                                                    |
| --- oriscus scapus           | :white_check_mark: | :x:                 | :x:                | :x:? TODO: check difference to oriscus                                                 |
| -- liquescent                | :white_check_mark: | :white_check_mark:  | :x:                | :white_check_mark:?                                                                    |
| --- ascending                | :white_check_mark: | :x:                 | :x:                | :white_check_mark:? TODO: maybe same as tails up/down                                  |
| --- descending               | :white_check_mark: | :x:                 | :x:                | :white_check_mark:? TODO: maybe same as tails up/down                                  |
| --- two tails down           | :x:                | :white_check_mark:  | :white_check_mark: | :white_check_mark:? TODO: maybe same as tails asc/desc                                 |
| --- two tails up             | :x:                | :white_check_mark:  | :white_check_mark: | :white_check_mark:? TODO: maybe same as tails asc/desc                                 |
| -- quadratum                 | :white_check_mark: | :x:                 | :x:                | :x: TODO: how to deal with it                                                          |
| - porrectus                  | implicit           | explicit            | explicit           | explicit TODO: algorithm                                                               |
| - accidental                 | :white_check_mark: | :white_check_mark:  | :white_check_mark: | :white_check_mark:                                                                     |
| -- flat                      | :white_check_mark: | :white_check_mark:  | :white_check_mark: | :white_check_mark:                                                                     |
| -- neutral                   | :white_check_mark: | :white_check_mark:  | :white_check_mark: | :white_check_mark:                                                                     |
| -- sharp                     | :white_check_mark: | :white_check_mark:  | :x:                | :white_check_mark:                                                                     |
| -- soft accidental           | :white_check_mark: | :x:                 | :x:                | :x:?                                                                                   |
| -- parenthesized accidental  | :white_check_mark: | :x:                 | :x:                | :x:?                                                                                   |
| - rhytmic sign               | :white_check_mark: | :white_check_mark:  | :x:                | :white_check_mark:?                                                                    |
| -- episema                   | :white_check_mark: | :white_check_mark:  | :x:                | :white_check_mark:?                                                                    |
| --- vertical                 | :white_check_mark: | :white_check_mark:  | :x:                | :white_check_mark:?                                                                    |
| ---- position tuning         | :white_check_mark: | :x:                 | :x:                | :x:                                                                                    |
| --- horizontal               | :white_check_mark: | :white_check_mark:  | :x:                | :white_check_mark:                                                                     |
| ---- position tuning         | :white_check_mark: | :white_check_mark:  | :x:                | :x:?                                                                                   |
| -- punctum mora              | :white_check_mark: | :white_check_mark:  | :x:                | :white_check_mark:                                                                     |
| - line break                 | :white_check_mark: | :x:                 | :x:                | :x:                                                                                    |
| - CONT                       | :x:                | :white_check_mark:  | :x:                | :x:?                                                                                   |
| - separation bar             | :white_check_mark: | :white_check_mark:  | :white_check_mark: | :white_check_mark:                                                                     |
| -- virgula                   | :white_check_mark: | :white_check_mark:  | :x:                | :x:? TODO: one type of sep. bar?                                                       |
| -- minimis bar               | :white_check_mark: | :white_check_mark:  | :x:                | :x:? TODO: one type of sep. bar?                                                       |
| -- small bar                 | :white_check_mark: | :white_check_mark:  | :x:                | :x:? TODO: one type of sep. bar?                                                       |
| -- maior bar                 | :white_check_mark: | :white_check_mark:  | :x:                | :x:? TODO: one type of sep. bar?                                                       |
| -- finallis bar              | :white_check_mark: | :white_check_mark:  | :x:                | :x:? TODO: one type of sep. bar?                                                       |
| -- minor bar                 | :white_check_mark: | :white_check_mark:  | :x:                | :x:? TODO: one type of sep. bar?                                                       |
| -- vertical episema modifier | :white_check_mark: | :x:                 | :x:                | :x:                                                                                    |
| -- bar brace modifier        | :white_check_mark: | :x:                 | :x:                | :x:                                                                                    |
