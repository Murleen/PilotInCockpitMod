import sys
import re
import os
import zipfile
import glob

def update_idle_animation(data, subs, orig_range, *ranges):
    pat_templ = r'\[Animation = idle\]\n\tRange={},{}\n\tNextAnimation="idle" *\n\tTransistion=(.*)\n\[end\]'
    rep_templ = r'[Animation = {}]\n\tRange={},{}\n\tNextAnimation="{}"\n\tTransistion=\1\n[end]'

    pattern = pat_templ.format(*orig_range)

    def name(i):
        return 'idle' + (str(i+1) if i > 0 else '')

    rep = '\r\n\r\n'.join(rep_templ.format(name(i), *r, name((i + 1) % len(ranges))) for i, r in enumerate(ranges))
    data, new_subs = re.subn(pattern, rep, data)
    return data, subs + new_subs

datadir = sys.argv[1]
builddir = sys.path[0] + '/build'

with zipfile.ZipFile('build.zip', mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
    textures = glob.glob('data/**/*.dds', recursive=True)
    for texture in textures:
        zf.write(texture, os.path.join('PilotInCockpit', texture))

    textures = [os.path.basename(t) for t in textures]

    models = set()

    for filename in glob.iglob(os.path.join(datadir, 'luascripts/worldobjects/bots/*.txt')):
        if 'b25d' in filename or 'npc' in filename:
            continue
        with open(filename, mode='r', encoding='cp1251') as f:
            data = f.read()
        models = models.union(re.findall(r'(?<!//)VisualImage=[0-9]+,"([^"]+)"', data))

    seasonmodels = {x for x in models if '%s' in x}
    models -= seasonmodels
    models |= {x.replace('%s', 'su') for x in seasonmodels}
    models |= {x.replace('%s', 'wi') for x in seasonmodels}

    newmodels = set()

    for filename in models:
        try:
            with open(datadir + '/' + filename, mode='rb') as f:
                data = f.read().decode('latin_1')
            modified = False
            for texture in textures:
                data, subs = re.subn(texture.replace('pilop', 'pilot').replace('p_pl', 't_pl').replace('t_ch', 'p_ch').replace('yaphat', 'yakhat'), texture, data, flags=re.I)
                if subs > 0:
                    modified = True
            if modified:
                data = re.sub('([0-9]\x0b\x00\x00\x00CanopyGlass)...(.)....(.).(..)...', '\\1\xff\xff\xff\\2\x00\x00\x00\xff\\3\x00\\4\x00\x00\x00', data)
                head, tail = os.path.split(filename)
                newfilename = head + '/_' + tail
                zf.writestr('PilotInCockpit/data/' + newfilename, data.encode('latin_1'))
                newmodels.add((filename, newfilename))
                newmodels.add((filename.replace('_su.', '_%s.').replace('_wi.', '_%s.'),
                               newfilename.replace('_su.', '_%s.').replace('_wi.', '_%s.')))

                with open(os.path.join(datadir, filename.replace('.mgm', '.txt')), mode='r', encoding='cp1251') as f:
                    txt = [l for l in f if 'lod=' not in l]
                zf.writestr('PilotInCockpit/data/' + newfilename.replace('.mgm', '.txt'), '\n'.join(txt).encode('cp1251'))
        except FileNotFoundError:
            pass

    chrfiles = set()

    for path, _, filenames in os.walk(os.path.join(datadir, 'luascripts/worldobjects/bots')):
        for filename in filenames:
            if 'b25d' in filename or 'npc' in filename:
                continue
            with open(path + '/' + filename, mode='r', encoding='cp1251') as f:
                data = f.read()
            modified = False
            for model in newmodels:
                data, subs = re.subn('VisualImage=2,"' + model[0] + '",true', '\g<0>\nVisualImage=1,"' + model[1] + '",true', data, flags=re.I)
                if subs > 0:
                    modified = True
            if modified:
                chrfiles = chrfiles.union(re.findall(r'Animator="([^"]*)"', data))
                shortpath = os.path.relpath(path, datadir).replace('\\', '/')
                zf.writestr('PilotInCockpit/data/' + shortpath + '/' + filename, data.encode('cp1251'))

    for c in chrfiles:
        with open(os.path.join(datadir, c), mode='r', encoding='cp1251') as f:
            data = f.read()
        data, subs = update_idle_animation(data, 0, (0, 1100), (0, 1000))
        data, subs = update_idle_animation(data, subs, (0, 1124), (0, 656), (760, 1124))
        data, subs = update_idle_animation(data, subs, (0, 1078), (0, 553), (758, 1078))
        data, subs = update_idle_animation(data, subs, (0, 1080), (0, 553), (758, 1080))
        if subs > 0:
            zf.writestr('PilotInCockpit/data/' + c, data.encode('cp1251'))

