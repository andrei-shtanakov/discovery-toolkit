# TODO

- [x] `slug: bank-coverage-key-markers` — машинный маркер `coverage_key` у каждой темы
      банка вопросов в `frames/*.md` + тест инвариантов полноты банка
      (issue #4, from: discovery).
- [x] `slug: gate-check-survives-foreign-input` — `gate_check.check()` тотален по форме
      frontmatter: не-мэппинг в `interview`/`coverage`, не-список в `sessions`,
      нехешируемые `frame`/значения coverage → finding GC-03/GC-04, не исключение
      (issue #18, from: discovery#49).
