```
usage: app.py [-h] [--csv CSV] [--first-column FIRST_COLUMN] [--last-column LAST_COLUMN] [--traits TRAITS] [--blueprint BLUEPRINT] [--out OUT]
              [--svg-width SVG_WIDTH] [--svg-height SVG_HEIGHT] [--use-names] [--attribute-number]
              [item]

NFT collection generator

Default input list: collection.csv
    Default name for 1 column is "name" and it used as name field in result json
    Default name for last column is "attribute_number" and it stored in result json if --attribute-name key exists
    All columns between first and last interpreted as traits columns
Default traits description: traits.json
Default out directory: ./out

positional arguments:
  item                  Index in input csv file to provide only this result instead of all output

options:
  -h, --help            show this help message and exit
  --csv CSV             CSV file with list of NFT combination
  --first-column FIRST_COLUMN
                        Name of first column in CSV (used as name)
  --last-column LAST_COLUMN
                        Name of last column in CSV (used as attribute_number)
  --traits TRAITS       JSON description of traits
  --blueprint BLUEPRINT
                        JSON template for generating output json file
  --out OUT             Output folder for results
  --svg-width SVG_WIDTH
                        Default svg width when convert to png, if svg used as background layer
  --svg-height SVG_HEIGHT
                        Default svg height when convert to png, if svg used as background layer
  --use-names           Use name column from csv as out filename
  --attribute-number    Store or not attribute_number column to result json
```

Order of searching filepaths in traits.json:

1. If "file" is object and conditional key exists and csv line matched this condition - than this filepath will be taken with highest priority.
2. If "file" is object without condition, path key will be taken with basic priority
3. If "file" is array of strings, all strings will be taken as path with basic priority
4. If "file" is string, this string will be taken as path with basic priority
