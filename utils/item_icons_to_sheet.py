import os
from PIL import Image
import dota_file_parser

# TODO: WRITE ALL OF THIS AS A RAKE TASK INSTEAD

print 'Expecting item icons to be in "items" (e.g. "items/blink.png")'
print 'Expecting item data to be in current folder (e.g. "items.txt")'
item_data = dota_file_parser.parse('items.txt')

item_list = {k:v['ID'] for k,v in item_data['DOTAAbilities'].iteritems() \
            if k.startswith('item_') and
                'ID' in v}

width = 88/2 # fullsize: 88
height = 64/2 # fullsize: 64
src_item_size = (0,0,88,64)
filename = "small_item_sheet"
images = []
for name,item_id in item_list.iteritems():
    # item_ = 5 characters
    name = name[5:]
    # TODO: only store 1 recipe image?
    if 'recipe' in name:
        name = 'recipe'
    img_name = os.path.join('items', name + '.png')
    try:
        im = Image.open(img_name).crop(src_item_size)
        im.thumbnail((width, height), Image.ANTIALIAS)
        images.append((item_id, im))
    except IOError as e:
        print e

max_id = max(item_list.values())
sheet_size = ((max_id + 1) * width, height)
sheet = Image.new("RGBA", sheet_size)
for item_id,img in images:
    sheet.paste(img, (item_id * width, 0))

sheet.save('{}.png'.format(filename))


# make CSS
# use wildcard for recipe styles
with open('{}.css.erb'.format(filename), 'wb') as f:
    for name,item_id in item_list.iteritems():
        f.write(""".{}-icon {{ background: url('<%= asset_path "{}.png" %>') no-repeat {}px 0px; width: {}px; height: {}px; }}\n""".format(name, filename, -item_id * width, width, height))
