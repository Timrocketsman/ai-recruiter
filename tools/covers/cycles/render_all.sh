#!/bin/bash
cd /tmp/claude-0/-home-user/ac9fbba0-b7d8-549e-a973-5b994798652b/scratchpad
declare -A M=([funnel]=avtomatizatsiya-voronki-prodazh [agents]=ii-agenty-v-telegram [channel]=avtomatizatsiya-telegram-kanala [seo]=seo-s-pomoschyu-neyroseti [si]=ii-teper-si-ukaz-trampa)
for k in "${!M[@]}"; do bl/blender -b --python cyc.py -- $k /home/user/ai-recruiter/media/covers/${M[$k]}.jpg ${1:-200} 2>&1 | grep -E "DONE|Traceback|rror:|line "; done; echo ALL_DONE
