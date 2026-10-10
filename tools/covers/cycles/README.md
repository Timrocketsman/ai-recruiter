# Обложки — Blender Cycles (трассировка лучей), основной генератор с 10.10
Почему: три.js даёт 3/5 — нет честного преломления, каустики, HDRI-отражений. Cycles даёт как у топовых студий.
Что внутри `cyc.py`: HDRI-студия Poly Haven (`studio_small_09_2k.hdr`, CC0) + площадные лампы (ключ, два цветных контровых в гамме сайта, кикер),
Principled-стекло (IOR 1.5, микро-царапины/пыль шумом в roughness + bump), хром с incorrectness-картой, пол с коат-слоем и неоновой сеткой,
задник — два мягких пятна cyan/magenta на #05070e, камера 50 мм f/2.2 с DOF, каустика (shadow caustics), AgX Punchy, композитор: fog glow, дисперсия линзы, виньетка.
Запуск (CPU 4 ядра ≈ 60–90 с/обложка при 200 сэмплах; на RTX 3090 через OptiX — секунды):
  blender -b --python cyc.py -- <funnel|agents|channel|seo|si> <out.jpg> [samples]
  ./render_all.sh 200
Новая статья: добавить ветку `elif MOTIF=="<id>"` со сценой (материалы: glass()/chrome()/neon(CY|MG)) и строку в render_all.sh.
