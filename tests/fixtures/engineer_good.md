---
spec_stage: discovery
status: draft
version: 1
generated_by: discovery-agent@claude-fable-5
generated_at: 2026-07-14
source_prompt_version: sha256:0000000000000000000000000000000000000000000000000000000000000000
validation: pending
approved_by: null
approved_at: null
owner_role: architect
approver: null
schema: discovery-brief
schema_version: 1
feeds: [system-assessment, tech-selection]
interview:
  frame: engineer
  sessions:
    - participant_role: platform-engineer
      date: 2026-07-14
      medium: sync
coverage:
  systems: covered
  interfaces: covered
  constraints: covered
  arch_preferences: covered
  risks: covered
  feasibility_review: covered
  gate_passed: true
open_questions: 1
blocking_open_questions: 0
conflicts: 0
traces_to: [customer_approved.md]
---

# Discovery Brief — dispatcher, engineer-фрейм (System Assessment)

Цели и требования — из approved customer-brief (`traces_to`); здесь только реальность систем.

## System Assessment

- **S-01** Полирепо-workspace `atp/`: 15 независимых git-репо, артефакты состояния on-disk
  (`.prograph/`, journal-файлы KB, git-метаданные). Владелец: ecosystem-TPM. Стабильно.
- **S-02** `prograph`: строит cross-project граф в `./.prograph/graph.db` (SQLite) +
  per-project facts. Владелец: prograph-автор. Стабильно, но схема БД не заморожена.

## Interfaces

- **IF-01** `traces: [S-01]` Git-метаданные читаются штатным git CLI/libgit2 — стабильный контракт.
- **IF-02** `traces: [S-02]` `graph.db` — прямое чтение SQLite; схема недокументирована,
  версионирования нет («так исторически»).

## Constraints

- **CON-01** Строго read-only доступ к проектным репо (граница из customer-brief NFR-01).
- **CON-02** Никаких демонов с записью в чужие директории; запуск только по требованию/cron.

## Architecture Preferences

- **AP-01** `traces: [S-02, CON-01]` Читать `.prograph/` как готовый источник графа, а не
  парсить репо заново — prograph уже решает эту задачу (отказ от дубля, см. ADR по X-01 upstream).

## Risks

- **RK-01** Tacit: схема `graph.db` менялась без нотиса дважды за квартал — чтение напрямую
  хрупко, ломается молча (знает только prograph-автор).

## Feasibility Review (по customer-brief)

- FR-01 (коллекторы, Must) — реализуемо: артефакты on-disk есть у всех пяти проектов; вердикт ок.
- FR-02 (TUI, Should) — реализуемо; вердикт ок.

## Open Questions

- **Q-01** `owner_role: architect` · `blocking: false` — пин схемы `graph.db`: просить
  prograph заморозить v1 или вендорить снапшот-ридер.

## Stakeholder Conflicts

Конфликтов не выявлено.
