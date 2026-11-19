---
spec_stage: discovery
status: draft
version: 1
generated_by: discovery-agent@claude-fable-5
generated_at: 2026-11-19
source_prompt_version: sha256:0000000000000000000000000000000000000000000000000000000000000000
validation: pass
approved_by: null
approved_at: null
owner_role: product
approver: null
schema: discovery-brief
schema_version: 1
feeds: [charter, requirements]
interview:
  frame: customer
  profile: feature
  sessions:
    - participant_role: repo-owner
      date: 2026-11-19
      medium: async
coverage:
  goals: covered
  personas: covered
  jobs: covered
  functions: covered
  nfr: covered
  constraints: covered
  success_metrics: covered
  out_of_scope: covered
  risks: missing
  gate_passed: true
open_questions: 1
blocking_open_questions: 0
conflicts: 0
traces_to: []
---

# Discovery Brief — экспорт словаря в CSV для Anki (профиль feature)

## Charter (→ Gate BR)

Фича в существующем приложении-словаре: выгрузить слова в CSV, который принимает Anki.
Блоки «стоить», «доказывать», «данные», «эксплуатация» отфильтрованы ответом «нет»;
«качество» — тоже, вопрос о владельце задан из короткого набора.

- **G-01** Повторять слова из словаря в Anki без ручного переноса.

## Personas

- **P-01** Владелец репо — единственный пользователь и сопровождающий. `owns: process, data, quality, operations`

## Jobs-to-be-done

- **J-01** `traces: [G-01]` «Когда набралось слов на неделю — хочу одной командой получить колоду, чтобы повторять в Anki».

## Functional Requirements

#### FR-01: Экспорт словаря в CSV   `traces: [G-01, J-01]`
**Priority**: 🔴 Must
**Preference**: «чтобы Anki просто съел файл»
**Acceptance**: файл импортируется в Anki без ручной правки; поля «слово», «перевод».

#### FR-02: Экспорт только новых слов   `traces: [J-01]`
**Priority**: 🟡 Could
**Acceptance**: повторный экспорт не дублирует уже выгруженные слова.

## Non-Functional

#### NFR-01: Только чтение словаря   `traces: [CON-01]`
**Category**: safety · **Target**: экспорт не меняет базу словаря.

#### NFR-02: Скорость и бюджет
**Category**: perf, cost
**N/A**: фильтр блока 4 — «нет»: «это пара сотен строк, работает как всё приложение»; отдельных требований к скорости и затратам нет.

## Constraints

- **CON-01** Чувствительных данных и регуляторных обязательств нет: фильтр блока 5 — «нет», «там только мои слова».

## Success Metrics

- **M-01** `traces: [G-01]` ручной перенос слов в Anki: каждую неделю → 0 раз.

## Out of Scope

- **OUT-01** Синхронизация с AnkiWeb и импорт обратно.

## Translation table

| Слова заказчика | Категория | Ограничение | Допущение | Подтверждает | Срок |
|---|---|---|---|---|---|
| «чтобы Anki просто съел файл» | делать | FR-01 | «съел» = импорт без ручной правки | repo-owner | 2026-11-26 |
| «базу трогать нельзя» | не делать | NFR-01 | — | — | — |
| «это пара сотен строк, работает как всё приложение» | стоить | NFR-02 | — | — | — |
| «там только мои слова» | доказывать | CON-01 | — | — | — |

## Open Questions

- **Q-01** `owner_role: product` · `blocking: false` — нужен ли выбор разделителя CSV.

## Stakeholder Conflicts

Конфликтов не выявлено.
