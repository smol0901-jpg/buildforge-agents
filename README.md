# BuildForge Agents

[![Docs](https://img.shields.io/badge/docs-system%20%2F%20kernel-3d8bfd)](https://smol0901-jpg.github.io/buildforge-agents/)
[![GitHub](https://img.shields.io/badge/GitHub-buildforge--agents-24292f)](https://github.com/smol0901-jpg/buildforge-agents)

**Ветка NEURAL_ARCHITECT_PREMIUM++** · ядро на базе
[v8 ULTIMATE](https://github.com/smol0901-jpg/neural-architect-premium-pages/blob/main/v8.txt) +
[INTENTION_ENGINE v8.4.00](https://smol0901-jpg.github.io/INTENTION_ENGINE_v8.4.00/)

Локальная мультиагентная система сборки: **Electron · C++ · C# · Python · HTML → EXE / ZIP / installer (Windows)**.
Эволюция [setuper](https://github.com/smol0901-jpg/setuper).

## Документация

Полное описание **системы, принципов, ядра, пайплайна, режимов и ограничений** (по коду репозитория):

**https://smol0901-jpg.github.io/buildforge-agents/**

## Что делает

1. Определяет тип проекта (`DetectorAgent`)
2. Проверяет toolchain (`DiagnosticianAgent`)
3. Готовит окружение и собирает через builders
4. Чинит типичные ошибки: memory → `known_errors.json` → (optional) LLM (`FixerAgent`)
5. Пакует ZIP/NSIS, smoke-проверяет EXE
6. Пишет уроки в SQLite `~/.buildforge/memory.db`

Успех только при наличии артефактов на диске (truth verification chain).

## Ядро NAP++

Каталог `neural_core/`: `v8.txt`, INTENTION_ENGINE (`FULL_PROMPT.md`, `00_…06_`), `BUILDFORGE_PERSONA.md`, `system_prompt()`.

Протоколы: DECOMPOSITION · TRUTH VERIFICATION CHAIN · VECTOR CORRECTION · SELF-HEALING.

Обращение: **Неиро** / BuildForge.  
Автор: Смолянинов А.В. · [@ASV_prod](https://t.me/ASV_prod) · [VK](https://vk.com/smolyaninovchef)

## Режимы

- **autopilot** — rules + memory + builders, без LLM
- **manual** — CLI / GUI
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

## Скачать

- Репозиторий: https://github.com/smol0901-jpg/buildforge-agents
- ZIP main: https://github.com/smol0901-jpg/buildforge-agents/archive/refs/heads/main.zip

## License

MIT · ASV_PROD
