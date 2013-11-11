import os
from PIL import Image
import dota_file_parser

print 'Expecting hero icons to be in "miniheroes" (e.g. "miniheroes/antimage.png")'
print 'Expecting hero data to be in current folder (e.g. "npc_heroes.txt")'
hero_data = dota_file_parser.parse('npc_heroes.txt')

hero_list = {k:v['HeroID'] for k,v in hero_data['DOTAHeroes'].iteritems() \
            if k.startswith('npc_dota_hero') and
                'HeroID' in v}

images = []
for name,hero_id in hero_list.iteritems():
    # npc_dota_hero_ = 14 characters
    name = name[14:]
    img_name = os.path.join('miniheroes', name + '.png')
    try:
        im = Image.open(img_name)
        images.append((hero_id, im))
    except IOError as e:
        print e

max_id = max(hero_list.values())
sheet_size = ((max_id + 1) * 32, 32)
sheet = Image.new("RGBA", sheet_size)
for hero_id,img in images:
    sheet.paste(img, (hero_id * 32, 0))

sheet.save('minihero_sheet.png')


# make CSS
with open('minihero_sheet.css.erb', 'wb') as f:
    for name,hero_id in hero_list.iteritems():
        f.write(""".{}-miniicon {{ background: url('<%= asset_path "minihero_sheet.png" %>') no-repeat {}px 0px; width: 32px; height: 32px; }}\n""".format(name, -hero_id * 32))
