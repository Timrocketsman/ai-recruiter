#!/usr/bin/env python3
"""Обложка статьи через ComfyUI (Qwen-Image-2512) на сервере. Запуск внутри my-ubuntu под gpu.lock:
  python3 cover_gen.py <slug> [--edit <blender_render.jpg>] [--seed N]
Промпт: prompts.json[slug] + _style; нет записи — текст промпта пишет Bonsai по заголовку/лиду статьи (роль article → JSON-поля).
Результат → site/media/covers/<slug>.jpg (1200×630, JPEG 90) → monetize_patch.py сам поставит под шапку и в og:image."""
import json, sys, time, random, urllib.request, os, subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); API="http://127.0.0.1:8188"
slug=sys.argv[1]; seed=int(sys.argv[sys.argv.index("--seed")+1]) if "--seed" in sys.argv else random.randrange(1<<31)
P=json.load(open(f"{HERE}/prompts.json"))
if slug not in P: sys.exit("нет промпта для %s — добавь в prompts.json или дай Bonsai сочинить (role article)" % slug)
if "--edit" in sys.argv:
    src=sys.argv[sys.argv.index("--edit")+1]; name=os.path.basename(src); subprocess.run(["cp",src,f"/opt/timlabs/render/ComfyUI/input/{name}"],check=True)
    wf=open(f"{HERE}/workflow_edit_api.json").read().replace("__INPUT__",name)
else:
    wf=open(f"{HERE}/workflow_t2i_api.json").read().replace("__PROMPT__",json.dumps(P[slug]+". "+P["_style"])[1:-1]).replace("__NEGATIVE__",P["_negative"])
wf=json.loads(wf.replace("__SEED__",str(seed)).replace("__SLUG__",slug)); wf.pop("_comment",None)
r=urllib.request.urlopen(urllib.request.Request(API+"/prompt",json.dumps({"prompt":wf}).encode(),{"Content-Type":"application/json"})); pid=json.load(r)["prompt_id"]
for _ in range(600):
    time.sleep(2); h=json.load(urllib.request.urlopen(API+"/history/"+pid))
    if pid in h:
        out=[o for n in h[pid]["outputs"].values() for o in n.get("images",[])][0]
        src=f"/opt/timlabs/render/ComfyUI/output/{out['subfolder']}/{out['filename']}"
        dst=f"/seo_agents/site/media/covers/{slug}.jpg"; os.makedirs(os.path.dirname(dst),exist_ok=True)
        subprocess.run(["convert",src,"-resize","1200x630^","-gravity","center","-extent","1200x630","-quality","90",dst],check=True)
        print("OK",dst,"seed",seed); break
else: sys.exit("timeout")
