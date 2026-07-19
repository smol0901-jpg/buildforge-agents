# Anti-freeze / paced load

## Caps (defaults)
| Metric | Critical (enter gentle) | Recover (leave gentle) |
|--------|-------------------------|------------------------|
| CPU    | **97%**                 | 90%                    |
| RAM    | **96%**                 | 90%                    |

## Behavior
1. Before every subprocess and between pipeline stages → `ResourceGuard.breath` / `stage_pause`.
2. If CPU≥97 or RAM≥96 → **gentle paced mode**:
   - wait with **exponential staged pauses** (1s → 2s → 4s → … ≤12s) until recover or max 180s
   - child processes on Windows get **BELOW_NORMAL** priority
   - env hints: `npm_config_jobs=1`, `CMAKE_BUILD_PARALLEL_LEVEL=1`, `MAX_JOBS=1`
3. While still gentle (between recover and critical) → short paced breaths between steps.
4. Events: `guard` + `log` from agent `resource_guard`; status payload includes `guard`.

## Env
See `.env.example` (`BUILDFORGE_CPU_CRITICAL`, `BUILDFORGE_RAM_CRITICAL`, …).

## Owner profile
Ollama + `hf.co/prism-ml/Bonsai-8B-gguf:Q1_0`, mode `neural`, max_fix_retries=2.
