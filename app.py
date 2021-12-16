import argparse
import csv
from io import BytesIO
import json
import os
from PIL import Image, ImageFile
from cairosvg import svg2png

ImageFile.LOAD_TRUNCATED_IMAGES = True

description="""NFT collection generator

Default input list: collection.csv
    Default name for 1 column is "name" and it used as name field in result json
    Default name for last column is "attribute_number" and it stored in result json if --attribute-name key exists
    All columns between first and last interpreted as traits columns
Default traits description: traits.json
Default out directory: ./out
"""
parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('--csv', help='CSV file with list of NFT combination', default='collection.csv')
parser.add_argument('--first-column', help='Name of first column in CSV (used as name)', default='name')
parser.add_argument('--last-column', help='Name of last column in CSV (used as attribute_number)', default='attribute_number')
parser.add_argument('--traits', help='JSON description of traits', default='traits.json')
parser.add_argument('--blueprint', help='JSON template for generating output json file', default='blueprint.json')
parser.add_argument('--out', help='Output folder for results', default='out')
parser.add_argument('--svg-width', help='Default svg width when convert to png, if svg used as background layer', default=1080, type=int)
parser.add_argument('--svg-height', help='Default svg height when convert to png, if svg used as background layer', default=1080, type=int)
parser.add_argument('--use-names', help='Default svg height when convert to png, if svg used as background layer', action='store_true')
parser.add_argument('--attribute-number', help='Store or not attribute_number column to result json', action='store_true')
parser.add_argument('item', help='Default svg height when convert to png, if svg used as background layer', default=None, type=int, nargs='?')

args = parser.parse_args()

# Populate collection properties from CSV file
collection = []
with open(args.csv, 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    header = None
    traits_name_index = None
    traits_attributes_index = None
    rn = 0
    for row in reader:
        if rn == 0:
            header = row
            try:
                traits_name_index = header.index(args.first_column)
            except ValueError as err:
                print("Can't find first column with given name. Please provide column, that will be used as 'name' column and start index")
                print("ValueError: %s" % err)
                exit()
            try:
                traits_attributes_index = header.index(args.last_column)
            except ValueError as err:
                print("Can't find last column with given name. Please provide column, that will be used as 'attribute_number' column and end index")
                print("ValueError: %s" % err)
                exit()
            rn+=1
        else:
            item = {}
            item['name'] = row[traits_name_index]
            item['attribute-number'] = row[traits_attributes_index]
            item['traits'] = dict(zip(header[traits_name_index+1:traits_attributes_index],row[traits_name_index+1:traits_attributes_index])) #obtain all columns between name and attribute_number
            collection.append(item)

#Load traits description
traits = None
with open(args.traits) as json_file:
    traits = json.load(json_file)

#Add filenames of traits to collection
for item in collection:
    for k,v in list(item['traits'].items()):
        if v != "":
            files = traits[k][v]['file']
            item['traits'][k] = {"name": v, "files": files if isinstance(files, list) else [files]}
        else:
            del item['traits'][k] #if empty trait name - remove from collection


# Generate Images and create json file from temlate
def open_img_file(filepath, background=None):
    if filepath.endswith('.svg'):
        width = args.svg_width
        height = args.svg_height
        if isinstance(background, Image.Image):
            width = background.width
            height = background.height
        new_bites = svg2png(file_obj=open(filepath, "rb"), unsafe=True, write_to=None, parent_width=width, parent_height=height)
        return Image.open(BytesIO(new_bites))
    return Image.open(filepath)

## load json template
blueprint = None
with open(args.blueprint) as json_file:
    blueprint = json.load(json_file)

indx = 1
saved = 0
for item in collection:

    if args.item is not None and args.item != indx:
        indx+=1
        continue

    outpath = "%s/%s" % (args.out,indx)
    if args.use_names == True:
        outpath = "%s/%s" % (args.out,item['name'])

    blueprint['name'] = item['name']
    blueprint['attributes'] = []

    if args.attribute_number == True:
        blueprint['attributes'].append({"trait_type":"attribute-number", "value":item["attribute-number"]})

    background = None
    for name,trait in item['traits'].items():
        blueprint['attributes'].append({"trait_type": name, "value": trait['name']})
        for file in trait['files']:
            if os.path.isfile(file):
                if background == None:
                    background = open_img_file(file).convert('RGBA')
                else:
                    img = open_img_file(file, background)
                    alpha_img = Image.new('RGBA', background.size)
                    alpha_img.paste(img, (0,0))
                    background = Image.alpha_composite(background, alpha_img)
    background.save("%s.png" % outpath)
    saved+=1

    with open("%s.json" % outpath, 'w') as outfile:
        json.dump(blueprint, outfile)
    indx+=1

print("Generated %s items" % saved)
