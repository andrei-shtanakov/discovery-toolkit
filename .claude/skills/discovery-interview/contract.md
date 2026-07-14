> **Vendored pin** — пиненая копия контракта, скопирована 2026-07-14 из
> `_cowork_output/contracts/2026-07-13-discovery-brief-contract-v0.1.md`
> (sha256: 35217e69ec4c489c4cb5bff0ff601c8035db97e4086ffcc959618822b0685905).
> Runtime/skill читает ТОЛЬКО эту копию, не `_cowork_output/` (правило корневого
> CLAUDE.md). При обновлении контракта — заменить копию целиком и обновить хеш.

# Discovery Brief — контракт выходного артефакта интервьюера (v0.1, DRAFT)

> Дата: 2026-07-13 · Статус: **Draft для заморозки** · Фаза 0 из
> `_cowork_output/decisions/2026-07-13-adr-discovery-interview-agent.md`
> Владелец: discovery-agent (авторит) · Потребитель: governance-слой (Gate BR/FRD/0b)
> Совместим с: SpecMeta v1 (`SPEC_META_CONTRACT=1`, spec-runner `spec.py`, C2-контракт 2026-07-05)

## TL;DR

1. **Не изобретаем парсер.** Discovery-brief переиспользует frontmatter SpecMeta v1 как есть.
   `meta_from_dict` фильтрует по `fields(SpecMeta)` и **игнорирует неизвестные ключи** (`spec.py:84`),
   поэтому discovery-специфику (`interview:`, `coverage:`) кладём отдельным блоком — ноль правок в
   spec-runner, ноль второго state-движка.
2. **Один brief → два gated-артефакта.** Интервью customer-фрейма даёт **Charter** (Gate BR) +
   черновик **Requirements** (FRD); engineer-фрейм — **System Assessment** (Gate 0b) + вход в Tech
   Selection (0a). Brief несёт секции, которые при входе в governance расщепляются по владельцам.
3. **Тело — в стиле FRD spec-runner + ID-трассируемость.** Требования как `FR-NN`/`NFR-NN` (те же
   Priority/Acceptance, что в `spec/requirements.md`), плюс discovery-секции (`G/P/J/M/CON/OUT/Q/X`).
   Инвариант: каждое `FR` трассируется в ≥1 `G`/`J`, каждая метрика `M` — в ≥1 `G`.
4. **Coverage-gate — машиночитаемый блок, а не проза.** `coverage:` во frontmatter фиксирует, какие
   разделы закрыты; `gate_passed: false`, пока все required (по профилю фрейма) не `covered`. Это тот
   самый главный тех-риск из ADR — вынесен в данные, чтобы CI/линтер проверял, а не человек на глаз.
5. **Конфликты и открытые вопросы — first-class.** `X-NN` (позиция A vs B + кто + статус) и `Q-NN`
   (owner + blocking) — обязательные секции. Агент их **поднимает, не усредняет**.

---

## 1. Frontmatter (SpecMeta v1 + discovery-расширение)

```yaml
---
# --- ядро SpecMeta v1 (as-is, spec-runner spec.py) ---
spec_stage: discovery            # upstream от requirements/design/tasks; governance-профиль знает стадию
status: draft                    # draft | in_review | approved — ЗЕРКАЛО git (git primary)
version: 1
generated_by: discovery-agent@claude-opus-4-8   # agent-id автора (<harness>@<model>)
generated_at: 2026-07-13
source_prompt_version: sha256:pending           # версия банка вопросов фрейма
validation: pending
approved_by: null                # actor/agent-id, записавший аппрув (семантика SpecMeta не меняется)
approved_at: null
owner_role: product              # CODEOWNERS-роль, аппрувящая brief (customer→product, engineer→architect)
approver: null                   # git-handle ЧЕЛОВЕКА, подтвердившего PR-merge (C2 REQ-402)
# --- discovery-расширение (unknown-keys, SpecMeta игнорирует; читает discovery/gate-check) ---
schema: discovery-brief
schema_version: 0.1
feeds: [charter, requirements]   # какие gated-артефакты governance порождает этот brief
interview:
  frame: customer                # customer | engineer  (профиль банка вопросов)
  sessions:                      # provenance (роли, НЕ имена по умолчанию — приватность, ADR risk #5)
    - participant_role: product-owner
      date: 2026-07-13
      medium: sync
coverage:                        # результат coverage-gate (см. §4) — required-набор по фрейму
  goals: covered
  personas: covered
  jobs: covered
  functions: covered
  nfr: covered
  constraints: covered
  success_metrics: covered
  risks: partial
  gate_passed: false             # true только когда все required = covered
open_questions: 2                # = число незакрытых Q-NN
blocking_open_questions: 1       # Q с blocking:true — governance-гейт не пройти, пока >0
conflicts: 1                     # число X-NN
traces_to: []                    # upstream-ссылки (KB prograph-vault, предыдущий charter)
---
```

**Правило зеркала:** `status`/`approved_by`/`approver` — машинное отражение git-состояния
(git — источник истины, как в [[project-spec-governance-layer]]). `gate-check` линтер сверяет.

---

## 2. Тело — секции и ID-конвенции

| Префикс | Секция | Обяз. (customer) | Обяз. (engineer) | Трассировка |
|---|---|:---:|:---:|---|
| `G-NN` | Цели | ✅ | — | — |
| `P-NN` | Персоны / стейкхолдеры | ✅ | ○ | — |
| `J-NN` | Jobs-to-be-done | ✅ | — | → G |
| `FR-NN` | Функциональные требования (MoSCoW) | ✅ | — | → ≥1 G/J |
| `NFR-NN` | Нефункциональные (категория + измеримая цель) | ✅ | ○ | → G/CON |
| `CON-NN` | Ограничения | ✅ | ✅ | — |
| `M-NN` | Success-метрики (измеримые) | ✅ | — | → ≥1 G |
| `OUT-NN` | Вне scope / non-goals | ✅ | ○ | — |
| `S-NN` | System Assessment (текущие системы/данные) | — | ✅ | — |
| `IF-NN` | Интерфейсы/контракты существующих систем | — | ✅ | → S |
| `AP-NN` | Архитектурные предпочтения/ограничения | — | ✅ | → S/CON |
| `RK-NN` | Риски (tacit-знание) | ○ | ✅ | — |
| `Q-NN` | Открытые вопросы (owner_role, blocking) | ✅ | ✅ | — |
| `X-NN` | Конфликты стейкхолдеров (A vs B, holders, status) | ✅ | ✅ | — |

✅ required · ○ optional · — не для этого фрейма.

**Инварианты (проверяет `gate-check`):**
- каждое `FR-NN` имеет `traces: [G-.. | J-..]` (≥1) — иначе требование «висит в воздухе»;
- каждая `M-NN` трассируется в ≥1 `G-NN`;
- каждый `Q-NN` имеет `owner_role` + `blocking: true|false`; каждый `X-NN` — `status: open|resolved`;
- `FR`/`NFR` несут `Priority` + `Acceptance Criteria` в формате FRD spec-runner (для чистого хендоффа
  в Gate FRD без переписывания).

---

## 3. Профили фреймов (данные, не код)

| | **customer** | **engineer** |
|---|---|---|
| Кого | заказчик / пользователь / product-owner | инженер / сотрудник, знающий текущие системы |
| Пространство | problem-space | solution-space |
| Банк вопросов (темы) | проблема → JTBD → персоны → функции (приоритет) → success-метрики → ограничения → что НЕ надо | текущие системы/данные → интерфейсы → ограничения инфры → архитектурные предпочтения → риски/tacit |
| Порождает | Charter (BR) + Requirements draft (FRD) | System Assessment (0b) + вход в Tech Selection (0a) |
| Аппрувит (owner_role) | product | architect |
| Анти-паттерн (запрет) | **не спрашивать про архитектуру** — заказчик её не проектирует | не собирать бизнес-цели заново — берём из customer-brief по `traces_to` |

---

## 4. Coverage-gate (главный тех-риск ADR, вынесен в данные)

Профиль фрейма задаёт `required`-набор секций. Правило:

```
gate_passed = ( все required-секции присутствуют И непустые )
              И ( каждое FR трассируется )
              И ( blocking_open_questions == 0 )
```

- `covered` = секция есть и непуста; `partial` = есть, но не покрывает чек-лист темы; `missing`.
- Незаблокированные `Q` (blocking:false) **не** валят gate — они легитимный перенос в governance.
- Заблокированные `Q` (blocking:true) валят: без ответа нельзя открывать Gate BR/FRD.

Смысл: агент физически не может «сдать» дырявый или наводяще-собранный brief — линтер режет до
человеческого ревью. Это дешевле, чем ловить пробел на Gate FRD.

---

## 5. Заполненный пример (customer-фрейм, продукт: `dispatcher`) — ИЛЛЮСТРАТИВНЫЙ

> Реконструкция из `COWORK_CONTEXT.md`, не авторитетный brief. Показывает форму контракта.

```markdown
---
spec_stage: discovery
status: draft
version: 1
generated_by: discovery-agent@claude-opus-4-8
generated_at: 2026-07-13
source_prompt_version: sha256:pending
validation: pending
approved_by: null
approved_at: null
owner_role: product
approver: null
schema: discovery-brief
schema_version: 0.1
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
  risks: partial
  gate_passed: false
open_questions: 2
blocking_open_questions: 1
conflicts: 1
traces_to: []
---

# Discovery Brief — dispatcher (ecosystem observability)

## Charter (→ Gate BR)
Проблема: состояние 15+ полирепо-проектов видно только ручным обходом git/артефактов;
TPM тратит время на «что сейчас в экосистеме». Scope: read-only агрегатор on-disk артефактов.

- **G-01** Ответ на «каково состояние экосистемы» без ручного обхода репозиториев.
- **G-02** Единая точка drill-down до проблемного проекта/связки.

## Personas
- **P-01** Ecosystem-TPM (Andrei) — primary; хочет состояние + рассинхроны.
- **P-02** Разработчик проекта — вторичный; хочет статус своего репо и его рёбер.

## Jobs-to-be-done
- **J-01** (→G-01) «Когда начинаю день — за 1 экран вижу, где что сломано/движется».
- **J-02** (→G-02) «Когда вижу проблему — проваливаюсь до конкретного шага/коммита».

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
#### NFR-02: Свежесть   **Category**: perf · **Target**: полный refresh < 5 c на 15 репо.

## Constraints
- **CON-01** Полирепо, без общего remote у корня; только чтение on-disk (CLAUDE.md границы).

## Success Metrics
- **M-01** (→G-01) time-to-answer «состояние экосистемы»: минуты ручного обхода → < 30 c.

## Out of Scope
- **OUT-01** Никакой оркестрации/запуска — это не executor (граница с Maestro/spec-runner).

## Open Questions
- **Q-01** `owner_role: architect` · `blocking: true` — граница dispatcher ↔ prograph ↔ appgraph
  по «графу/наблюдаемости» не решена (COWORK_CONTEXT overlap-триада). Без решения scope плывёт.
- **Q-02** `owner_role: product` · `blocking: false` — нужен ли web-UI помимо TUI.

## Stakeholder Conflicts
- **X-01** `status: open` — «наблюдаемость» claim: dispatcher (read-on-disk дашборд) vs prograph
  (cross-project graph, MCP) vs appgraph. Позиция A: dispatcher = единый view. Позиция B: prograph
  уже строит граф связей → dispatcher дублирует. Держатели: TPM / prograph-автор. → эскалация в ADR.
```

---

## 6. Рекомендуемые действия (для заморозки контракта)

- **[решить]** Один artefact `discovery-brief` с секциями Charter+Requirements внутри — или сразу два
  файла на входе в governance? Предлагаю: **один brief**, расщепление на Charter/Requirements — при
  открытии гейтов (меньше церемонии на discovery-стадии, ADR risk #1).
- **[зафиксировать]** `spec_stage: discovery` как новую governance-стадию (в spec-runner SPEC_STAGES
  НЕ добавлять — это стадия governance-профиля, не exec-профиля).
- **[golden-фикстура]** По образцу C2 (`spec_meta_contract_v1.md`) сделать
  `discovery_brief_v0.1.md` + ожидаемый разбор — чтобы `gate-check` линтер тестировался против эталона.
- **[gate-check]** Правила из §2/§4 (трассировка FR→G/J, coverage required-набор, blocking-Q) — как
  правила линтера governance-слоя ([[reference-scope-linter-oss]] как база).
- **[приватность]** Политика `interview.sessions`: по умолчанию роли, не имена (ADR risk #5) — решить
  до интервью сотрудников.
- **[grounding]** `traces_to` заполнять ссылками в `prograph-vault`, чтобы не переспрашивать известное
  (пересечение с robin-runtime — общий субстрат).

---

*Источники:* `_cowork_output/decisions/2026-07-13-adr-discovery-interview-agent.md` (фаза 0),
`_cowork_output/spec-runner-c2-specmeta-contract/spec/{requirements,design}.md` (SpecMeta v1 поля,
unknown-key-ignore, `owner_role`/`approver` семантика), `spec-runner/spec/FORMAT.md` (FRD-стиль),
[[project-spec-governance-layer]] (гейты BR/FRD/0b, git-аппрув), `COWORK_CONTEXT.md` (пример dispatcher).
