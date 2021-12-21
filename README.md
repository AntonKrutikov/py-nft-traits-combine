```
usage: app.py [-h] [--csv CSV] [--traits TRAITS] [--blueprint BLUEPRINT] [--out OUT] [--svg-width SVG_WIDTH] [--svg-height SVG_HEIGHT]
              [--use-names USE_NAMES]
              item

NFT collection generator

Default input list: collection.csv
Default traits description: traits.json
Default out directory: ./out

positional arguments:
  item                  Default svg height when convert to png, if svg used as background layer

options:
  -h, --help            show this help message and exit
  --csv CSV             CSV file with list of NFT combination
  --traits TRAITS       JSON description of traits
  --blueprint BLUEPRINT
                        JSON template for generating output json file
  --out OUT             Output folder for results
  --svg-width SVG_WIDTH
                        Default svg width when convert to png, if svg used as background layer
  --svg-height SVG_HEIGHT
                        Default svg height when convert to png, if svg used as background layer
  --use-names USE_NAMES
                        Default svg height when convert to png, if svg used as background layer
```

Order of searching filepaths in traits.json:

1. If "file" is object and conditional key exists and csv line matched this condition - than this filepath will be taken with highest priority.
2. If "file" is object without condition, path key will be taken with basic priority
3. If "file" is array of strings, all strings will be taken as path with basic priority
4. If "file" is string, this string will be taken as path with basic priority
