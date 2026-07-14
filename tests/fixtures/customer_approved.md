---
spec_stage: discovery
status: approved
version: 1
generated_by: discovery-agent@claude-fable-5
generated_at: 2026-07-14
source_prompt_version: sha256:0000000000000000000000000000000000000000000000000000000000000000
validation: pass
approved_by: governance-gate@claude-fable-5
approved_at: 2026-07-14
owner_role: product
approver: andrei-shtanakov
schema: discovery-brief
schema_version: 1
feeds: [charter, requirements]
interview:
  frame: customer
  sessions:
    - participant_role: ecosystem-tpm
      date: 2026-07-13
      medium: sync
coverage:
  goals: covered
  personas: covered
  jobs: covered
  functions: covered
  nfr: covered
  constraints: covered
  success_metrics: covered
  out_of_scope: covered
  risks: partial
  gate_passed: true
open_questions: 2
blocking_open_questions: 0
conflicts: 0
traces_to: []
---

# Discovery Brief — dispatcher (ecosystem observability)

## Charter (→ Gate BR)

Проблема: состояние 15+ полирепо-проектов видно только ручным обходом git/артефактов;
TPM тратит время на «что сейчас в экосистеме». Scope: read-only агрегатор on-disk артефактов.

- **G-01** Ответ на «каково состояние экосистемы» без ручного обхода репозиториев.
- **G-02** Единая точка drill-down до проблемного проекта/связки.

## Personas

- **P-01** Ecosystem-TPM — primary; хочет состояние + рассинхроны.
- **P-02** Разработчик проекта — вторичный; хочет статус своего репо и его рёбер.

## Jobs-to-be-done

- **J-01** `traces: [G-01]` «Когда начинаю день — за 1 экран вижу, где что сломано/движется».
- **J-02** `traces: [G-02]` «Когда вижу проблему — проваливаюсь до конкретного шага/коммита».

## Functional Requirements

#### FR-01: Коллекторы состояния по всем проектам   `traces: [G-01, J-01]`
**Priority**: 🔴 Must
**Acceptance**: коллекторы на atp/Maestro/arbiter/spec-runner/proctor; читают on-disk артефакты.

#### FR-02: Read-only TUI со сводкой + drill-down   `traces: [G-01, G-02, J-02]`
**Priority**: 🟠 Should
**Acceptance**: экран-сводка + переход к деталям проекта; нет мутаций.

## Non-Functional

#### NFR-01: Строго read-only   `traces: [CON-01]`
**Category**: safety · **Target**: 0 записей в проектные репо; только чтение.

#### NFR-02: Свежесть
**Category**: perf · **Target**: полный refresh < 5 c на 15 репо.

## Constraints

- **CON-01** Полирепо, без общего remote у корня; только чтение on-disk (границы CLAUDE.md).

## Success Metrics

- **M-01** `traces: [G-01]` time-to-answer «состояние экосистемы»: минуты ручного обхода → < 30 c.

## Out of Scope

- **OUT-01** Никакой оркестрации/запуска — это не executor (граница с Maestro/spec-runner).

## Risks

- **RK-01** Пересечение по «наблюдаемости» с prograph/appgraph может размыть scope.

## Open Questions

- **Q-01** `owner_role: architect` · `blocking: false` — граница dispatcher ↔ prograph ↔ appgraph
  по «графу/наблюдаемости»: решение перенесено в governance (см. X-01, resolved).
- **Q-02** `owner_role: product` · `blocking: false` — нужен ли web-UI помимо TUI.

## Stakeholder Conflicts

- **X-01** `status: resolved` — «наблюдаемость» claim: dispatcher (read-on-disk дашборд) vs
  prograph (cross-project graph). Решено ADR: dispatcher = view, prograph = граф; дубля нет.
