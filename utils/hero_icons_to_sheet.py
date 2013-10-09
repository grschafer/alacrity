import os
from PIL import Image
import dota_file_parser

# data from dota2 files: resource/flash3/images/heroes
print 'Expecting hero icons to be in "heroes" (e.g. "heroes/antimage.png")'
print 'Expecting hero data to be in current folder (e.g. "npc_heroes.txt")'
hero_data = dota_file_parser.parse('npc_heroes.txt')

hero_list = {k:v['HeroID'] for k,v in hero_data['DOTAHeroes'].iteritems() \
            if k.startswith('npc_dota_hero') and
                'HeroID' in v}

width = 128/2 # fullsize: 128
height = 72/2 # fullsize: 72
filename = "small_hero_sheet"
images = []
for name,hero_id in hero_list.iteritems():
    # npc_dota_hero_ = 14 characters
    name = name[14:]
    img_name = os.path.join('heroes', name + '.png')
    try:
        im = Image.open(img_name)
        im.thumbnail((width, height), Image.ANTIALIAS)
        images.append((hero_id, im))
    except IOError as e:
        print e

max_id = max(hero_list.values())
sheet_size = ((max_id + 1) * width, height)
sheet = Image.new("RGBA", sheet_size)
for hero_id,img in images:
    sheet.paste(img, (hero_id * width, 0))

sheet.save('{}.png'.format(filename))


# make CSS
with open('{}.css.erb'.format(filename), 'wb') as f:
    for name,hero_id in hero_list.iteritems():
        f.write(""".{}-icon {{ background: url('<%= asset_path "{}.png" %>') no-repeat {}px 0px; width: {}px; height: {}px; }}\n""".format(name, filename, -hero_id * width, width, height))
