"""A reproducible same-input comparison, with no hand-authored page geometry."""
from pathlib import Path
import json
import shutil

root=Path(__file__).resolve().parents[1]
before=root/'examples/visual-defaults'
after=root/'examples/launch-studio'
after.mkdir(exist_ok=True)
for name in ('announcement.md','source.json','prompts.json'):
    shutil.copyfile(before/name,after/name)
for name in ('inputs','assets'):
    shutil.copytree(before/name,after/name,dirs_exist_ok=True)
plan=json.loads((before/'plan.json').read_text())
# Auto profile, inferred from the existing product illustration briefs.
plan['visual_defaults'].pop('profile',None)
plan['visual_defaults'].pop('tone',None)
(after/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
print('Same claims, data and two images; automatic product-launch treatment.')
