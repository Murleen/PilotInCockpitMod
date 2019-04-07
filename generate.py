import sys
import re
import os
import shutil
import zipfile

datadir = sys.argv[1]
builddir = sys.path[0] + '/build'

with zipfile.ZipFile('build.zip', mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
    textures = os.listdir(sys.path[0] + '/data/graphics/textures/common')
    for texture in textures:
        zf.write(sys.path[0] + '/data/graphics/textures/common/' + texture, 'PilotInCockpit/data/graphics/textures/common/' + texture)

    newmodels = set()

    for path, _, filenames in os.walk(datadir + "graphics/characters"):
        for filename in filenames:
            if re.fullmatch('(pilot|gunner)_.*\.mgm', filename):
                with open(path + '/' + filename, mode='rb') as f:
                    data = f.read().decode('latin_1')
                modified = False
                for texture in textures:
                    data, subs = re.subn(texture.replace('pilop', 'pilot'), texture, data, flags=re.I)
                    if subs > 0:
                        modified = True
                if modified:
                    shortpath = path.partition(datadir)[2].replace('\\', '/')
                    newfilename = filename.replace('pilot', 'pilop').replace('gunner', 'gunnep')
                    zf.writestr('PilotInCockpit/data/' + shortpath + '/' + newfilename, data.encode('latin_1'))
                    newmodels.add((shortpath + '/' + filename.replace('_su.', '_%s.').replace('_wi.', '_%s.'),
                                   shortpath + '/' + newfilename.replace('_su.', '_%s.').replace('_wi.', '_%s.')))

    for path, _, filenames in os.walk(datadir + 'luascripts/worldobjects/bots'):
        for filename in filenames:
            with open(path + '/' + filename, mode='r', encoding='cp1251') as f:
                data = f.read()
            modified = False
            for model in newmodels:
                data, subs = re.subn('VisualImage=2,"' + model[0] + '",true', '\g<0>\nVisualImage=1,"' + model[1] + '",true', data, flags=re.I)
                if subs > 0:
                    modified = True
            if modified:
                shortpath = path.partition(datadir)[2].replace('\\', '/')
                zf.writestr('PilotInCockpit/data/' + shortpath + '/' + filename, data.encode('cp1251'))
