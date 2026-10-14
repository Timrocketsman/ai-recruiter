# Видеопрезентация «TimLabs: как всё устроено» (14.10.2026)

Сцены — `timlabs_architecture.html` (HTML + CSS-анимации, цвета сайта, 1920×1080, ~1:43, 8 сцен: устройства,
агенты, офис из трёх этажей, сайт, контент-план и кросс-постинг, контроль). Запись — `record.js` (Playwright Chromium,
`recordVideo` → webm), затем H.264:

    NODE_PATH=$(npm root -g) node tools/presentation/record.js        # из папки с index.html → vid/*.webm
    ffmpeg -i vid/*.webm -c:v libx264 -crf 20 -pix_fmt yuv420p -movflags +faststart -an timlabs_architecture.mp4

Звука нет: текст подписей (`.cap`, заголовки сцен) — готовый сценарий для озвучки голосом Тима (F5-TTS на сервере,
`/opt/timlabs/render/voice_ctl.sh ensure`), потом `ffmpeg -i video.mp4 -i voice.wav -c:v copy -c:a aac`.
Правка содержания — только в HTML (тайминги сцен в массиве `T` внизу файла).
