#!/usr/bin/env python3
"""Prepare the existing Qwen cover workflow; every CLI renders through cover_neuro.

No import-time work, direct GPU HTTP, input copies into shared Comfy, or live-site writes.
"""
import json
import hashlib
import io
import os
from pathlib import Path
import random
import re
import sys

HERE = Path(__file__).resolve().parent


def prepare(slug, *, seed=None, edit=None, prompts=None):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,159}', str(slug)):
        raise ValueError('invalid cover slug')
    seed = random.randrange(1 << 31) if seed is None else int(seed)
    p = prompts if prompts is not None else json.loads((HERE / 'prompts.json').read_text())
    if slug not in p:
        raise ValueError('cover prompt missing: ' + slug)
    inputs = []
    input_sizes = []
    if edit:
        source = Path(edit).resolve(strict=True)
        if not source.is_file():
            raise ValueError('edit input is not a regular image')
        raw_input = source.read_bytes()
        inputs.append(dict(path=str(source), sha256=hashlib.sha256(raw_input).hexdigest(),
                           size=len(raw_input)))
        from PIL import Image
        with Image.open(io.BytesIO(raw_input)) as image:
            input_sizes.append(list(image.size))
        template = HERE / 'workflow_edit_api.json'
        raw = template.read_text().replace('__INPUT__', source.name)
    else:
        template = HERE / 'workflow_t2i_api.json'
        raw = template.read_text()
        raw = raw.replace('__PROMPT__', json.dumps(p[slug] + '. ' + p['_style'])[1:-1])
        raw = raw.replace('__NEGATIVE__', json.dumps(p['_negative'])[1:-1])
    workflow = json.loads(raw.replace('__SEED__', str(seed)).replace('__SLUG__', slug))
    workflow.pop('_comment', None)
    steps = os.environ.get('COVER_STEPS')
    if steps is not None:
        if not 1 <= int(steps) <= 40:
            raise ValueError('cover steps outside existing 1–40 limit')
        for node in workflow.values():
            if node.get('class_type') == 'KSampler':
                node['inputs']['steps'] = int(steps)
    return dict(slug=slug, seed=seed, workflow=workflow, inputs=inputs, input_sizes=input_sizes,
                template_sha256=hashlib.sha256(template.read_bytes()).hexdigest())


def main(argv=None):
    sys.path.insert(0, '/seo_agents/tools')
    import cover_neuro
    return cover_neuro.main(sys.argv[1:] if argv is None else argv)


if __name__ == '__main__':
    raise SystemExit(main())
