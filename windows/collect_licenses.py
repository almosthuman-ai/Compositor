"""Copy dependency license texts into a built distribution, preserving package provenance."""
from importlib.metadata import distributions
from pathlib import Path
import json, shutil, sys

target=Path(sys.argv[1])/'third-party-licenses'; target.mkdir(parents=True,exist_ok=True); records=[]
for distribution in distributions():
    name=distribution.metadata.get('Name','unknown'); version=distribution.version
    files=[]
    for entry in distribution.files or []:
        if any(part.lower().startswith(('license','copying','notice')) for part in entry.parts) and '.dist-info' in str(entry):
            source=Path(distribution.locate_file(entry))
            if source.is_file():
                destination=target/(name+'-'+version)/Path(*entry.parts[1:]); destination.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(source,destination); files.append(str(destination.relative_to(target)))
    records.append({'package':name,'version':version,'license':distribution.metadata.get('License-Expression') or distribution.metadata.get('License'),'files':files})
(target/'index.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
for name in ('ffmpeg',):
    source=Path(__file__).parent/'licenses'/name
    if source.exists():shutil.copytree(source,target/name,dirs_exist_ok=True)
glitch=Path(__file__).parent/'compositor/glitch_assets'
(target/'glitch-temple').mkdir(exist_ok=True)
for name in ('LICENSE.txt','origin.json'):shutil.copyfile(glitch/name,target/'glitch-temple'/name)
print(f'Collected notices for {len(records)} installed packages')
