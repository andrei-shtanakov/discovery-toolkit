# discovery-toolkit

Skill-бандл стадии **discovery/elicitation** для ATP-экосистемы: интервью со
стейкхолдером → структурированный `discovery-brief` → вход в governance-гейты
(BR/FRD — фрейм customer; 0b/0a — фрейм engineer). Методология-как-файлы, по паттерну
robin-toolkit; stateful-runtime — отдельный будущий репо `discovery` (author ≠ execute).

## Состав

```
.claude/skills/discovery-interview/
  SKILL.md            # оркестрация: фрейм → интервью → извлечение → coverage-gate → выдача
  frames/customer.md  # problem-space: банк вопросов, чек-листы, запрет вопросов про архитектуру
  frames/engineer.md  # solution-space: банк вопросов, feasibility-проход, запрет пересбора целей
  contract.md         # пиненая копия discovery-brief-contract v0.1 (единственный источник схемы для skill)
```

Интервьюер останавливается на brief: он **не пишет** tasks.md/design — компиляция вниз
делегируется governance-слою. Конфликты стейкхолдеров поднимаются как `X-NN`, не
усредняются; coverage-gate (контракт §4) обязателен перед выдачей.

## Provenance

Решения и план — в cowork-workspace (dev-only, skill их не читает):
`_cowork_output/decisions/2026-07-13-adr-discovery-interview-agent.md`,
`_cowork_output/plans/2026-07-13-discovery-agent-flow-and-test-strategy.md`,
`_cowork_output/contracts/2026-07-13-discovery-brief-contract-v0.1.md` (v0.1, вендорен
в `contract.md`).
