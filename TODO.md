# TODO

- [x] `slug: bank-coverage-key-markers` — машинный маркер `coverage_key` у каждой темы
      банка вопросов в `frames/*.md` + тест инвариантов полноты банка
      (issue #4, from: discovery).
- [x] `slug: gate-check-survives-foreign-input` — `gate_check.check()` тотален по форме
      frontmatter: не-мэппинг в `interview`/`coverage`, не-список в `sessions`,
      нехешируемые `frame`/значения coverage → finding GC-03/GC-04, не исключение
      (issue #18, from: discovery#49).
- [x] `slug: preference-constraint-translation` — контракт v1.2: Preference → гипотеза → `Q-NN` исследования (GC-17), `> ` для инструкций в банке @owner:github:andrei-shtanakov (PR #29) @id:preference-constraint-translation
      Подробно: `**Preference**` дословно,
      гипотеза-ограничение в Acceptance/Target, число — `Q-NN` исследования (GC-17);
      в банке `- ` — вопрос человеку, `> ` — инструкция составителю
      (issue #28, from: discovery#71).
- [x] `slug: customer-frame-enterprise-questionnaire` — контракт v1.3: банк customer = опросник владельца (9 блоков на прежних coverage-ключах), `## Translation table` как итог discovery, критерии «Discovery завершён» → GC-18…GC-21 (PR #31) @owner:github:andrei-shtanakov @id:customer-frame-enterprise-questionnaire
      Подробно: колонки «архитектурное решение» нет — вывод в `Q-NN` для architect;
      механические критерии — error (таблица, допущения с подтверждающим и сроком,
      четыре категории, perf/cost числом с единицей, владельцы `owns:`), семантические —
      чек-лист фрейма (issue #30, from: devtools#764).
- [x] `slug: gc18-translation-header-check` — GC-18 сверяет заголовок translation table с колонками контракта v1.3 (порядок, без учёта регистра) @owner:github:andrei-shtanakov @id:gc18-translation-header-check
      Подробно: колонки читаются по позиции — чужой или пропущенный заголовок раньше
      молча «съедал» первую строку данных (issue #32, from: discovery-toolkit#31, ревью Copilot).
- [x] `slug: customer-frame-feature-profile` — контракт v1.4: профиль `feature` фрейма customer — короткий набор + вопросы-фильтры блоков 4–8 разметкой банка, `**N/A**` у NFR/CON закрывает GC-08/GC-20, GC-22 (PR #36) @owner:github:andrei-shtanakov @id:customer-frame-feature-profile
      Подробно: строка `<!-- profile: feature; short: …; filter: … -->` — отдельно от
      маркера темы (старый парсер рантайма её пропускает); GC-19/GC-21 не ослаблены —
      ответ на фильтр даёт строку таблицы, вопросы о владельцах в коротком наборе
      (issue #35, from: discovery#86 ← devtools#816).
- [x] `slug: gc05-upstream-read-total` — нечитаемый upstream engineer-брифа (не UTF-8, исчез при чтении) — находка GC-12, не исключение из `check()` (PR #37) @owner:github:andrei-shtanakov @id:gc05-upstream-read-total
      Подробно: последний путь падения после #18 — чтение upstream для GC-05;
      discovery снимет ограду `cli._lint_brief` на `approve` после перепина
      (issue #34, from: discovery, todo://discovery/approve-lint-fence).
