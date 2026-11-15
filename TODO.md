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
