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

item_img_size = (0,0,88,64)
images = []
for name,item_id in item_list.iteritems():
    # item_ = 5 characters
    name = name[5:]
    # TODO: only store 1 recipe image?
    if 'recipe' in name:
        name = 'recipe'
    img_name = os.path.join('items', name + '.png')
    try:
        im = Image.open(img_name).crop(item_img_size)
        images.append((item_id, im))
    except IOError as e:
        print e

max_id = max(item_list.values())
sheet_size = ((max_id + 1) * 88, 64)
sheet = Image.new("RGBA", sheet_size)
for item_id,img in images:
    sheet.paste(img, (item_id * 88, 0))

sheet.save('item_sheet.png')


# make CSS
# use wildcard for recipe styles
with open('item_sheet.css.erb', 'wb') as f:
    for name,item_id in item_list.iteritems():
        f.write(""".{}-icon {{ background: url('<%= asset_path "item_sheet.png" %>') no-repeat {}px 0px; width: 88px; height: 64px; }}\n""".format(name, -item_id * 88))
