# discovery-toolkit

Skill-бандл стадии **discovery/elicitation** для ATP-экосистемы: интервью со
стейкхолдером → структурированный `discovery-brief` → вход в governance-гейты
(BR/FRD — фрейм customer; 0b/0a — фрейм engineer). Методология-как-файлы, по паттерну
robin-toolkit; stateful-runtime — отдельный будущий репо `discovery` (author ≠ execute).

## Состав

```
DISCOVERY-BRIEF-CONTRACT.md   # КАНОН: контракт discovery-brief v1 (frozen 2026-07-14)
gate_check.py                 # линтер брифов: правила GC-01…GC-14 из контракта §5
.claude/skills/discovery-interview/
  SKILL.md                    # оркестрация: фрейм → grounding → интервью → coverage-gate → выдача
  frames/customer.md          # problem-space: банк вопросов, чек-листы, запрет вопросов про архитектуру
  frames/engineer.md          # solution-space: банк вопросов, feasibility-проход, запрет пересбора целей
  contract.md                 # пиненая копия канона (самодостаточность skill'а; синк проверяется тестом)
tests/
  fixtures/                   # golden: customer_good/approved, engineer_good; bad_gcNN_* — по правилу на файл
  test_gate_check.py          # L0 (SpecMeta unknown-keys) + L1 (gate-check против фикстур)
  test_contract_sync.py       # копия контракта в skill не разъехалась с каноном
  test_frames_markers.py      # банк вопросов фреймов полон относительно coverage-гейта
```

## Использование

```sh
uv run gate_check.py path/to/discovery-brief.md   # линт брифа; exit 1 при ошибках
uv run pytest                                      # L0+L1 против golden-фикстур
```

Интервьюер останавливается на brief: он **не пишет** tasks.md/design — компиляция вниз
делегируется governance-слою. Конфликты стейкхолдеров поднимаются как `X-NN`, не
усредняются; coverage-gate обязателен перед выдачей.

## Provenance

Решения и план — в cowork-workspace (dev-only, shipped-файлы его не читают):
`_cowork_output/decisions/2026-07-13-adr-discovery-interview-agent.md`,
`_cowork_output/plans/2026-07-13-discovery-agent-flow-and-test-strategy.md`,
`_cowork_output/contracts/2026-07-13-discovery-brief-contract-v0.1.md` (черновик v0.1;
канон v1 — в этом репо).
