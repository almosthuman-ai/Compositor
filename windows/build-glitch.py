"""Build the locally supplied Glitch Temple canvas engine; no runtime Node dependency."""
from pathlib import Path
import argparse,json,subprocess,shutil

parser=argparse.ArgumentParser(); parser.add_argument('--source',type=Path); args=parser.parse_args()
root=Path(__file__).resolve().parent; stage=root/'local/glitch-build'; stage.mkdir(parents=True,exist_ok=True)
source=root/'glitch-engine/vendor'
if args.source:
    upstream=args.source.resolve(); (source/'src').mkdir(parents=True,exist_ok=True)
    for name in ('studio.ts','LivePreview.tsx'): shutil.copyfile(upstream/'src'/name,source/'src'/name)
    shutil.copyfile(upstream/'LICENSE',source/'LICENSE')
    (source/'commit.txt').write_text(subprocess.check_output(['git','rev-parse','HEAD'],cwd=upstream,text=True).strip(),encoding='utf-8')
(stage/'studio.ts').write_text((source/'src/studio.ts').read_text(encoding='utf-8'),encoding='utf-8')
engine=(source/'src/LivePreview.tsx').read_text(encoding='utf-8')
engine=engine[engine.index('import { petsciiPalette'):engine.index('export const LivePreview =')]
engine=engine.replace('const context = canvas.getContext("2d", { alpha: false })!;', 'const context = canvas.getContext("2d")!;\n  context.imageSmoothingEnabled = false;')
engine+='\nexport { fittedSource, cloneSurface, compositeLayers, blendSource, applyEffect, targetSurface };\n'
(stage/'effects.ts').write_text(engine,encoding='utf-8')
(stage/'bridge.ts').write_text((root/'glitch-engine/bridge.ts').read_text(encoding='utf-8'),encoding='utf-8')
assets=root/'compositor/glitch_assets'; assets.mkdir(exist_ok=True)
subprocess.run(['npx.cmd','--yes','esbuild@0.25.12',str(stage/'bridge.ts'),'--bundle','--format=iife','--global-name=TempleEngine','--target=chrome110',f'--outfile={assets / "engine.js"}'],cwd=root,check=True)
commit=(source/'commit.txt').read_text(encoding='utf-8').strip()
shutil.copyfile(source/'LICENSE',assets/'LICENSE.txt')
(assets/'origin.json').write_text(json.dumps({'name':'Glitch Temple','author':'Tai Mei','repository':'https://github.com/taimei886/glitch-temple','commit':commit,'engine':'Canvas','adaptations':['Full-resolution rendering outside React','Nearest source sampling','Qt command bridge']},indent=2),encoding='utf-8')
