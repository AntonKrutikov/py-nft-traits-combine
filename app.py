import argparse
import csv
from io import BytesIO
import json
import os
from threading import Condition
from PIL import Image, ImageFile
from cairosvg import svg2png
from tqdm import tqdm
import collections

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
parser.add_argument('--use-names', help='Use name column from csv as out filename', action='store_true')
parser.add_argument('--attribute-number', help='Store or not attribute_number column to result json', action='store_true')
parser.add_argument('item', help='Index in input csv file to provide only this result instead of all output', default=None, type=int, nargs='?')

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
    traits = json.load(json_file, object_pairs_hook=collections.OrderedDict)

#Add filenames of traits to collection
for item in collection:
    original_traits = item['traits'].copy() #needed for simplier checking conditional files
    for k,v in list(item['traits'].items()):
        if v != "" and k in traits and v in traits[k]:
            files = traits[k][v]['file']
            item['traits'][k] = {"name": v, "hidden": traits[k][v].get('hidden', False), "exclude": traits[k][v].get('exclude', []) }
            #single file as string
            if isinstance(files, str):
                item['traits'][k]["files"] = {"condition":[], "path": [files]}
            #array of files or conditional files
            if isinstance(files, list):
                match_files = []
                for f in files:
                    #search if suitable conditions, overwrite any overs
                    if isinstance(f, dict) and 'adapted-to' in f:
                        condition = f['adapted-to'] if isinstance(f['adapted-to'],list) else [f['adapted-to']]
                        for c in condition:
                            for _,t in original_traits.items():
                                if c == t:
                                    match_files = {"condition":condition, "path": f['path'] if isinstance(f['path'], list) else [f['path']]}
                    #search for default in object style, array style or string style. Takes first match
                    elif isinstance(f, dict) and 'adapted-to' not in f and len(match_files) == 0:
                        match_files = {"condition":[], "path": f['path'] if isinstance(f['path'], list) else [f['path']]}
                    elif isinstance(f, list) and len(match_files) == 0:
                        match_files = {"condition":[], "path": f}
                    elif isinstance(f, str) and len(match_files) == 0:
                        match_files = {"condition":[], "path": [f]}
                item['traits'][k]["files"] = match_files
            #check excluded
            for e in item['traits'][k]['exclude']:
                for _,t in original_traits.items():
                    if t == e:
                        # del item['traits'][k]
                        # Not delete raise error message and exit
                        print("Error: Found exclude '%s' option for trait '%s'.'%s', but this exists in input CSV row. Item with name '%s' skipped." % (e, k,v, item['name']))
                        item['broken'] = True
    
        else:
            del item['traits'][k] #if empty trait name - remove from collection

for item in collection:
    if 'broken' in item:
        
        collection.remove(item)

print(len(collection))

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

#If item arg proided - reduce collection to 1 item
if args.item is not None:
    collection = [collection[args.item-1]]
indx = 1
saved = 0
with tqdm(total=len(collection)) as pbar:
    for item in collection:
        outpath = "%s/%s" % (args.out,indx)
        if args.use_names == True:
            outpath = "%s/%s" % (args.out,item['name'])

        blueprint['name'] = item['name']
        blueprint['attributes'] = []

        if args.attribute_number == True:
            blueprint['attributes'].append({"trait_type":"attribute-number", "value":item["attribute-number"]})

        background = None
        for name,trait in item['traits'].items():
            if trait['hidden'] == False:
                blueprint['attributes'].append({"trait_type": name, "value": trait['name']})
            for file in trait['files']['path']:
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
        pbar.update(1)

print("Generated %s items" % saved)