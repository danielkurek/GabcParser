# Comparison of the formats

| Feature                      | GABC               | S-GABC              | MEI-GABC           |
| ---------------------------- | ------------------ | ------------------- | ------------------ |
| **Lyrics**                   |                    |                     |                    |
| - normal text                | :white_check_mark: | :white_check_mark:  | :white_check_mark: |
| - formatting                 | :white_check_mark: | :white_check_mark:  | :x:                |
| -- bold                      | :white_check_mark: | :white_check_mark:  | :x:                |
| -- italic                    | :white_check_mark: | :white_check_mark:  | :x:                |
| -- color                     | :white_check_mark: | :white_check_mark:  | :x:                |
| -- underline                 | :white_check_mark: | :white_check_mark:  | :x:                |
| -- small caps                | :white_check_mark: | :white_check_mark:  | :x:                |
| -- teletype                  | :white_check_mark: | :x:                 | :x:                |
| -- above line text           | :white_check_mark: | :x:                 | :x:                |
| -- arbitrary TeX             | :white_check_mark: | :x:                 | :x:                |
| -- syllable centering        | :white_check_mark: | :x:                 | :x:                |
| -- euouae tag                | :white_check_mark: | :x:                 | :x:                |
| -- special symbols           | :white_check_mark: | :white_check_mark:  | :x:                |
| **Music**                    |                    |                     |                    |
| - music tag                  | :white_check_mark: | :white_check_mark:  | :x:                |
| - clef                       | :white_check_mark: | :white_check_mark:  | :white_check_mark: |
| -- flat clef                 | :white_check_mark: | :white_check_mark:  | :x:                |
| -- `C` and `F` clef          | :white_check_mark: | :white_check_mark:  | :white_check_mark: |
| -- linked clef               | :white_check_mark: | :x:                 | :x:                |
| - note                       | :white_check_mark: | :white_check_mark:  | :white_check_mark: |
| -- pitch                     | relative           | relative            | absolute           |
| -- square/rhombus shape      | :white_check_mark: | :white_check_mark:  | :white_check_mark: |
| -- repetition                | :white_check_mark: | :x:                 | :x:                |
| -- virga                     | :white_check_mark: | :white_check_mark:  | :white_check_mark: |
| --- left/right               | :white_check_mark: | :white_check_mark:  | :white_check_mark: |
| --- explicit virga           | :x:                | :white_check_mark:? | :white_check_mark: |
| -- empty note                | :white_check_mark: | :x:                 | :x:                |
| -- note accent               | :white_check_mark: | :x:                 | :x:                |
| -- custom ledger line        | :white_check_mark: | :x:                 | :x:                |
| - uncertain reading          | :x:                | :white_check_mark:  | :x:                |
| - custos                     | :white_check_mark: | :white_check_mark:  | :white_check_mark: |
| -- explicit pitch            | :white_check_mark: | :white_check_mark:  | :white_check_mark: |
| -- implicit pitch            | :white_check_mark: | :white_check_mark:  | :x:                |
| - note spacing               | :white_check_mark: | :white_check_mark:  | :x:                |
| -- zero width space          | :white_check_mark: | :white_check_mark:  | :x:                |
| -- normal space              | :white_check_mark: | :x:                 | :x:                |
| -- factor space              | :white_check_mark: | :white_check_mark:  | :x:                |
| - note shape                 | :white_check_mark: | :white_check_mark:  | :white_check_mark: |
| -- strophicus                | :white_check_mark: | :white_check_mark:  | :x:                |
| -- quilisma                  | :white_check_mark: | :white_check_mark:  | :x:                |
| -- oriscus                   | :white_check_mark: | :white_check_mark:  | :x:                |
| --- oriscus scapus           | :white_check_mark: | :x:                 | :x:                |
| -- liquescent                | :white_check_mark: | :white_check_mark:  | :x:                |
| --- ascending                | :white_check_mark: | :x:                 | :x:                |
| --- descending               | :white_check_mark: | :x:                 | :x:                |
| --- two tails down           | :x:                | :white_check_mark:  | :white_check_mark: |
| --- two tails up             | :x:                | :white_check_mark:  | :white_check_mark: |
| -- quadratum                 | :white_check_mark: | :x:                 | :x:                |
| - porrectus                  | implicit           | explicit            | explicit           |
| - accidental                 | :white_check_mark: | :white_check_mark:  | :white_check_mark: |
| -- flat                      | :white_check_mark: | :white_check_mark:  | :white_check_mark: |
| -- neutral                   | :white_check_mark: | :white_check_mark:  | :white_check_mark: |
| -- sharp                     | :white_check_mark: | :white_check_mark:  | :x:                |
| -- soft accidental           | :white_check_mark: | :x:                 | :x:                |
| -- parenthesized accidental  | :white_check_mark: | :x:                 | :x:                |
| - rhytmic sign               | :white_check_mark: | :white_check_mark:  | :x:                |
| -- episema                   | :white_check_mark: | :white_check_mark:  | :x:                |
| --- vertical                 | :white_check_mark: | :white_check_mark:  | :x:                |
| ---- position tuning         | :white_check_mark: | :x:                 | :x:                |
| --- horizontal               | :white_check_mark: | :white_check_mark:  | :x:                |
| ---- position tuning         | :white_check_mark: | :white_check_mark:  | :x:                |
| -- punctum mora              | :white_check_mark: | :white_check_mark:  | :x:                |
| - line break                 | :white_check_mark: | :x:                 | :x:                |
| - CONT                       | :x:                | :white_check_mark:  | :x:                |
| - separation bar             | :white_check_mark: | :white_check_mark:  | :white_check_mark: |
| -- virgula                   | :white_check_mark: | :white_check_mark:  | :x:                |
| -- minimis bar               | :white_check_mark: | :white_check_mark:  | :x:                |
| -- small bar                 | :white_check_mark: | :white_check_mark:  | :x:                |
| -- maior bar                 | :white_check_mark: | :white_check_mark:  | :x:                |
| -- finallis bar              | :white_check_mark: | :white_check_mark:  | :x:                |
| -- minor bar                 | :white_check_mark: | :white_check_mark:  | :x:                |
| -- vertical episema modifier | :white_check_mark: | :x:                 | :x:                |
| -- bar brace modifier        | :white_check_mark: | :x:                 | :x:                |
