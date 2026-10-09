# Обложки статей — 3D (three.js, физичный свет)
Стекло/хром/неон, PBR-материалы, зеркальный пол (Reflector), мягкие тени (VSM), ACES.
Запуск: `npm i three@0.169.0` в этой папке → `python3 -m http.server 8777` отсюда → `node r3d.js [мотив]`.
Мотивы (`?k=`): funnel, agents, channel, seo, si — сцена в `scene.html`, соответствие slug — в `r3d.js`.
Новая статья ИИ-рубрики: добавить мотив в scene.html и строку в map → `media/covers/<slug>.jpg`;
`tools/monetize_patch.py` сам ставит картинку под шапкой и в og:image.
