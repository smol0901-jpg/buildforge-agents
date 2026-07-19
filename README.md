# BuildForge Agents

[![Live page](https://img.shields.io/badge/LIVE%20PAGE-3D%20Immersion-00e5ff)](https://smol0901-jpg.github.io/buildforge-agents/) [![GitHub](https://img.shields.io/badge/GitHub-buildforge--agents-7c5cff)](https://github.com/smol0901-jpg/buildforge-agents)
**Ветка NEURAL_ARCHITECT_PREMIUM++** · ядро на базе
[v8 ULTIMATE](https://github.com/smol0901-jpg/neural-architect-premium-pages/blob/main/v8.txt) +
[INTENTION_ENGINE v8.4.00](https://smol0901-jpg.github.io/INTENTION_ENGINE_v8.4.00/)

Мультиагентная фабрика: **Electron · C++ · C# · Python · HTML → EXE + installers**.
Эволюция [setuper](https://github.com/smol0901-jpg/setuper).

## 🎬 Cinematic 3D page

Immersions-style WebGL presentation (Three.js · scroll-camera · agent orbits):

**https://smol0901-jpg.github.io/buildforge-agents/**

- Source: [`docs/index.html`](docs/index.html)
- Download / ZIP / author ASV_PROD on the page
- GitHub Pages: branch `main` → `/docs`

## Ядро NAP++
Каталог `neural_core/`: `v8.txt`, INTENTION_ENGINE (`FULL_PROMPT.md`, `00_…06_`), `BUILDFORGE_PERSONA.md`, `system_prompt()`.

Протоколы: DECOMPOSITION · TRUTH VERIFICATION CHAIN · VECTOR CORRECTION · SELF-HEALING.

Обращение: **Неиро** / BuildForge. Автор: Смолянинов А.В. · [@ASV_prod](https://t.me/ASV_prod) · [VK](https://vk.com/smolyaninovchef)

## Режимы
- **autopilot** — rules + memory, без LLM
- **manual** — CLI / GUI кнопки
- **neural** — Ollama / GGUF / OpenAI-compatible

## Старт
```bat
git clone https://github.com/smol0901-jpg/buildforge-agents.git
cd buildforge-agents
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python app.py --gui
python app.py -p D:\MyApp -m autopilot -t exe+installer
python app.py -p D:\MyApp -m neural --llm ollama --model qwen2.5:7b
python app.py --serve-phone --port 8787
```
Телефон (Wi‑Fi): `http://<IP-ПК>:8787`

## Пайплайн
DETECT → DIAGNOSE → PREPARE → BUILD → FIX-LOOP → PACKAGE → VERIFY → REMEMBER

## License
MIT · ASV_PROD
