"""L0/L1: golden-фикстуры против gate_check (контракт DISCOVERY-BRIEF-CONTRACT.md §5-6)."""

from pathlib import Path

import pytest

from gate_check import check, parse_brief

FIXTURES = Path(__file__).parent / "fixtures"


def run(name: str):
    path = FIXTURES / name
    return check(path.read_text(encoding="utf-8"), base_dir=path.parent)


def errors(findings):
    return [f for f in findings if f.level == "error"]


# --- L1: good-фикстуры проходят гейт ---------------------------------------

@pytest.mark.parametrize(
    "name",
    ["customer_good.md", "customer_approved.md", "customer_feature_good.md", "engineer_good.md"],
)
def test_good_fixture_passes(name):
    findings = run(name)
    assert errors(findings) == [], [str(f) for f in findings]


# --- L1: каждая bad-фикстура ломает ровно своё правило ----------------------

@pytest.mark.parametrize(
    ("name", "expected_rule"),
    [
        ("bad_gc04_missing_key.md", "GC-04"),
        ("bad_gc05_covered_empty.md", "GC-05"),
        ("bad_gc06_untraced_fr.md", "GC-06"),
        ("bad_gc09_q_no_owner.md", "GC-09"),
        ("bad_gc10_counter_mismatch.md", "GC-10"),
        ("bad_gc11_blocking_gate.md", "GC-11"),
        ("bad_gc12_upstream_draft.md", "GC-12"),
        ("bad_gc15_validation_stale.md", "GC-15"),
        ("bad_gc16_unresolvable_traces.md", "GC-16"),
        ("bad_gc17_dangling_research_ref.md", "GC-17"),
        ("bad_gc18_assumption_unconfirmed.md", "GC-18"),
        ("bad_gc19_category_missing.md", "GC-19"),
        ("bad_gc20_perf_without_number.md", "GC-20"),
        ("bad_gc21_owner_missing.md", "GC-21"),
        ("bad_gc22_na_outside_feature.md", "GC-22"),
    ],
)
def test_bad_fixture_fails_exactly_its_rule(name, expected_rule):
    errs = errors(run(name))
    assert errs, f"{name}: ожидалась ошибка {expected_rule}, но линтер молчит"
    assert {f.rule for f in errs} == {expected_rule}, [str(f) for f in errs]


# --- L1: точечные правила без фикстур-файлов --------------------------------

def test_gc14_solution_space_leak_is_warning_not_error():
    text = (FIXTURES / "customer_good.md").read_text(encoding="utf-8") + (
        "\n## Systems\n\n- **S-01** Заказчик принёс архитектуру.\n"
    )
    findings = check(text, base_dir=FIXTURES)
    assert errors(findings) == []
    assert any(f.rule == "GC-14" and f.level == "warning" for f in findings)


def test_unresolvable_upstream_is_gc16_error_plus_gc12_warning():
    text = (FIXTURES / "engineer_good.md").read_text(encoding="utf-8").replace(
        "traces_to: [customer_approved.md]", "traces_to: [no/such/brief.md]"
    ).replace("validation: pass", "validation: fail")
    findings = check(text, base_dir=FIXTURES)
    assert {f.rule for f in errors(findings)} == {"GC-16"}, [str(f) for f in findings]
    assert any(f.rule == "GC-12" and f.level == "warning" for f in findings)


def test_traces_to_as_yaml_string_is_normalized():
    text = (FIXTURES / "engineer_good.md").read_text(encoding="utf-8").replace(
        "traces_to:\n  - discovery-brief-customer.md", "traces_to: customer_approved.md"
    ).replace("traces_to: [customer_approved.md]", "traces_to: customer_approved.md")
    findings = check(text, base_dir=FIXTURES)
    assert errors(findings) == [], [str(f) for f in findings]


@pytest.mark.parametrize("payload", [b"\xff\xfe\x00bad", b"---\nstatus: \xff\n---\n"])
def test_non_utf8_upstream_is_gc12_finding_not_crash(tmp_path, payload):
    """Нечитаемый upstream — находка GC-12, не UnicodeDecodeError (issue #34)."""
    (tmp_path / "bin.md").write_bytes(payload)
    text = (FIXTURES / "engineer_good.md").read_text(encoding="utf-8").replace(
        "traces_to: [customer_approved.md]", "traces_to: [bin.md]"
    ).replace("validation: pass", "validation: fail")
    errs = errors(check(text, base_dir=tmp_path))
    assert [(f.rule, f.ref) for f in errs] == [("GC-12", "bin.md")], [str(f) for f in errs]


def test_upstream_vanished_after_resolve_is_gc12_finding(monkeypatch):
    """OSError между is_file() и чтением (TOCTOU) — тоже GC-12, не исключение."""
    text = (FIXTURES / "engineer_good.md").read_text(encoding="utf-8").replace(
        "validation: pass", "validation: fail"
    )
    real_read_text = Path.read_text

    def read_text(self, *args, **kwargs):
        if self.name == "customer_approved.md":
            raise FileNotFoundError(self)
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    errs = errors(check(text, base_dir=FIXTURES))
    assert [(f.rule, f.ref) for f in errs] == [("GC-12", "customer_approved.md")], [
        str(f) for f in errs
    ]


def test_traversal_and_absolute_refs_rejected():
    from gate_check import _resolve_ref

    assert _resolve_ref("/etc/hosts", FIXTURES) is None
    escape = "../" * 8 + "etc/hosts"
    assert _resolve_ref(escape, FIXTURES) is None


def test_missing_frontmatter_is_gc01():
    findings = check("# просто markdown без frontmatter\n")
    assert [f.rule for f in findings] == ["GC-01"]


# --- L0: unknown-keys совместимость со SpecMeta (meta_from_dict-семантика) ---

SPECMETA_V1_FIELDS = {
    "spec_stage", "status", "version", "generated_by", "generated_at",
    "source_prompt_version", "validation", "approved_by", "approved_at",
}


@pytest.mark.parametrize("name", ["customer_good.md", "engineer_good.md"])
def test_specmeta_core_present_and_extension_is_unknown_keys(name):
    brief = parse_brief((FIXTURES / name).read_text(encoding="utf-8"))
    assert brief is not None
    # ядро SpecMeta v1 присутствует целиком — бриф без потерь читается spec-runner'ом
    assert SPECMETA_V1_FIELDS <= set(brief.meta)
    # discovery-специфика едет ТОЛЬКО unknown-keys (meta_from_dict их игнорирует)
    extension = set(brief.meta) - SPECMETA_V1_FIELDS
    assert {"schema", "schema_version", "interview", "coverage"} <= extension


# --- L1: чужой ввод — форма frontmatter произвольна, линтер тотален (issue #18) --

def customer_with(replacements: dict[str, str]) -> str:
    text = (FIXTURES / "customer_good.md").read_text(encoding="utf-8")
    for old, new in replacements.items():
        assert old in text, f"фикстура не содержит {old!r}"
        text = text.replace(old, new)
    return text


def test_interview_scalar_is_gc03_error_not_crash():
    meta_head = customer_with({}).split("\n---", 1)[0]
    interview_block = meta_head[meta_head.index("interview:"):]
    interview_block = interview_block[: interview_block.index("\ncoverage:")]
    text = customer_with({interview_block: "interview: customer"})
    findings = check(text, base_dir=FIXTURES)
    assert any(f.rule == "GC-03" and f.ref == "interview" for f in errors(findings)), [
        str(f) for f in findings
    ]


def test_coverage_scalar_is_gc04_error_not_crash():
    meta_head = customer_with({}).split("\n---", 1)[0]
    coverage_block = meta_head[meta_head.index("coverage:"):]
    coverage_block = coverage_block[: coverage_block.index("\ntraces_to:")]
    text = customer_with({coverage_block: "coverage: everything"})
    findings = check(text, base_dir=FIXTURES)
    assert any(f.rule == "GC-04" and f.ref == "coverage" for f in errors(findings)), [
        str(f) for f in findings
    ]


def test_sessions_scalar_is_single_gc03_error():
    meta_head = customer_with({}).split("\n---", 1)[0]
    sessions_block = meta_head[meta_head.index("  sessions:"):]
    sessions_block = sessions_block[: sessions_block.index("\ncoverage:")]
    text = customer_with({sessions_block: "  sessions: interviewed"})
    gc03 = [f for f in errors(check(text, base_dir=FIXTURES)) if f.rule == "GC-03"]
    assert [f.ref for f in gc03] == ["interview.sessions"], [str(f) for f in gc03]


def test_unhashable_frame_and_coverage_values_do_not_crash():
    text = customer_with({"  frame: customer": "  frame: [customer]"})
    findings = check(text, base_dir=FIXTURES)
    assert any(f.rule == "GC-03" and f.ref == "interview.frame" for f in errors(findings))

    text = customer_with({"  goals: covered": "  goals: [covered]"})
    findings = check(text, base_dir=FIXTURES)
    assert any(f.rule == "GC-04" and f.ref == "coverage.goals" for f in errors(findings))


# --- L1: предпочтение → гипотеза → число как Q-NN исследования (v1.2, issue #28) --

RESEARCH_NFR = (
    "**Preference**: «чтобы обновлялось мгновенно»\n"
    "**Category**: perf · **Target**: полный refresh не дольше значения из Q-02."
)
NFR_02_TARGET = "**Category**: perf · **Target**: полный refresh < 5 c на 15 репо."


def test_research_ref_to_open_q_passes():
    """Preference + гипотеза со ссылкой на открытый Q — полная запись, ошибок нет."""
    findings = check(customer_with({NFR_02_TARGET: RESEARCH_NFR}), base_dir=FIXTURES)
    assert errors(findings) == [], [str(f) for f in findings]
    assert not [f for f in findings if f.rule == "GC-17"]


def test_research_ref_to_resolved_q_is_warning():
    """Q закрыт — число найдено, ссылку пора заменить значением: warning, не error."""
    text = customer_with(
        {
            NFR_02_TARGET: RESEARCH_NFR,
            "`blocking: false` — нужен ли web-UI": "`blocking: false` · `resolved: true` — нужен ли web-UI",
            "open_questions: 2": "open_questions: 1",
        }
    )
    findings = check(text, base_dir=FIXTURES)
    assert errors(findings) == [], [str(f) for f in findings]
    assert any(f.rule == "GC-17" and f.level == "warning" and f.ref == "NFR-02" for f in findings)


def test_research_ref_in_fr_acceptance_and_metric_is_checked():
    """GC-17 смотрит FR, NFR и M одинаково."""
    text = customer_with(
        {
            "**Acceptance**: экран-сводка": "**Acceptance**: по Q-07; экран-сводка",
            "минуты ручного обхода → < 30 c.": "baseline из Q-08 → < 30 c.",
        }
    )
    refs = {f.ref for f in errors(check(text, base_dir=FIXTURES)) if f.rule == "GC-17"}
    assert refs == {"FR-02", "M-01"}


# --- L1: enterprise-фрейм заказчика — translation table и владельцы (v1.3, issue #30) --

STOIT_ROW = (
    "| «обновляться должно быстро» | стоить | NFR-02 | «быстро» = полный refresh до 5 с "
    "| ecosystem-tpm | 2026-07-20 |"
)


def gc_errors(text: str, rule: str) -> list[str]:
    return [f.message for f in errors(check(text, base_dir=FIXTURES)) if f.rule == rule]


def test_gc18_missing_table_is_single_error():
    text = customer_with({"## Translation table": "## Заметки"})
    assert gc_errors(text, "GC-18") == ["секции нет или в ней нет строк"]
    assert gc_errors(text, "GC-19") == []  # без таблицы категории не считаются


@pytest.mark.parametrize(
    ("row", "fragment"),
    [
        (STOIT_ROW.replace("NFR-02", "NFR-09"), "NFR-09"),
        (STOIT_ROW.replace("NFR-02", "G-01"), "G-01"),
        (STOIT_ROW.replace("NFR-02", "быстрый отклик"), "не ссылается на ID"),
        (STOIT_ROW.replace("| стоить |", "| скорость |"), "вне словаря"),
        (STOIT_ROW.replace("«обновляться должно быстро»", "—"), "нет слов заказчика"),
        (STOIT_ROW.replace(" | 2026-07-20 |", " |"), "колонок"),
    ],
)
def test_gc18_row_defects(row, fragment):
    messages = gc_errors(customer_with({STOIT_ROW: row}), "GC-18")
    assert any(fragment in m for m in messages), messages


@pytest.mark.parametrize(
    "target",
    [
        "p95 до 2 с",
        "до 500 запросов/день",
        "95%",
        "$300 в месяц",
        "не более 40 000 ₽ в месяц",
        "до 20 °C",
        "не хуже значения из Q-02",
    ],
)
def test_gc20_accepts_number_with_unit_or_research_ref(target):
    text = customer_with(
        {"**Target**: полный refresh < 5 c на 15 репо.": f"**Target**: {target}."}
    )
    assert gc_errors(text, "GC-20") == []


def test_gc20_ignores_non_numeric_categories():
    """safety-цель без числа легитимна: «0 записей» не обязана быть метрикой."""
    text = customer_with({"**Category**: safety · **Target**: 0 записей": "**Category**: safety · **Target**: ни одной записи"})
    assert gc_errors(text, "GC-20") == []


def test_gc21_owner_may_be_open_question():
    """Владелец не назван — открытый Q с тем же owns закрывает GC-21."""
    text = customer_with(
        {
            " `owns: data`": "",
            "`blocking: false` — нужен ли web-UI": "`blocking: false` · `owns: data` — нужен ли web-UI",
        }
    )
    assert gc_errors(text, "GC-21") == []


def test_enterprise_rules_do_not_apply_to_engineer_frame():
    findings = run("engineer_good.md")
    assert not {f.rule for f in findings} & {"GC-18", "GC-19", "GC-20", "GC-21"}


def test_gc20_nfr_without_category_is_error():
    """Отсутствие Category не выключает GC-20 (ревью PR #31)."""
    text = customer_with({"**Category**: perf · **Target**: полный": "**Target**: полный"})
    assert "нет **Category**: без неё perf/cost-цель не проверить" in gc_errors(text, "GC-20")


def test_gc20_multiple_categories_include_perf():
    text = customer_with(
        {
            "**Category**: perf · **Target**: полный refresh < 5 c на 15 репо.":
            "**Category**: safety, perf · **Target**: полный refresh — быстро."
        }
    )
    assert len(gc_errors(text, "GC-20")) == 1


@pytest.mark.parametrize("target", ["не хуже, чем у M-01 сегодня", "в рамках CON-01 и политик"])
def test_gc20_record_id_digits_are_not_numbers(target):
    text = customer_with(
        {"**Target**: полный refresh < 5 c на 15 репо.": f"**Target**: {target}."}
    )
    assert len(gc_errors(text, "GC-20")) == 1


def test_gc21_resolved_question_does_not_name_owner():
    text = customer_with(
        {
            " `owns: data`": "",
            "`blocking: false` — нужен ли web-UI": (
                "`blocking: false` · `owns: data` · `resolved: true` — нужен ли web-UI"
            ),
            "open_questions: 2": "open_questions: 1",
        }
    )
    assert gc_errors(text, "GC-21") == ["владелец не назван: нет P или открытого Q с этим owns"]


def test_gc20_requires_perf_and_cost_targets_to_exist():
    """Пункт чек-листа «латентность, объём, бюджет числами» не закрывается пустотой."""
    text = customer_with({"**Category**: cost ·": "**Category**: safety ·"})
    assert gc_errors(text, "GC-20") == ["нет ни одной NFR категории cost"]


def test_gc18_row_without_leading_pipe_is_still_checked():
    """GFM-строка без ведущей трубы не выпадает из проверки (fail-closed)."""
    row = STOIT_ROW.replace("NFR-02", "NFR-99")
    messages = gc_errors(customer_with({STOIT_ROW: row.lstrip("| ")}), "GC-18")
    assert any("NFR-99" in m for m in messages), messages


HEADER_ROW = "| Слова заказчика | Категория | Ограничение | Допущение | Подтверждает | Срок |"


@pytest.mark.parametrize(
    "header",
    [
        HEADER_ROW.replace("| Категория | Ограничение |", "| Ограничение | Категория |"),
        "| «за один экран вижу» | делать | FR-01 | — | — | — |",  # данные вместо заголовка
    ],
)
def test_gc18_header_must_match_contract_columns(header):
    """Колонки читаются по позиции — чужой заголовок не пропускается (issue #32)."""
    messages = gc_errors(customer_with({HEADER_ROW: header}), "GC-18")
    assert len(messages) == 1 and "заголовок" in messages[0], messages


def test_gc18_header_is_case_insensitive():
    assert gc_errors(customer_with({HEADER_ROW: HEADER_ROW.lower()}), "GC-18") == []


def test_gc18_header_only_table_is_empty():
    table_rows = customer_with({}).split(HEADER_ROW + "\n|---|---|---|---|---|---|\n")[1]
    data = table_rows.split("\n\n## ")[0] + "\n"
    messages = gc_errors(customer_with({data: ""}), "GC-18")
    assert messages == ["секции нет или в ней нет строк"], messages


# --- L1: профиль feature — фича в существующем репо (v1.4, issue #35) ---------

NA_NFR = (
    "**Category**: perf, cost\n"
    "**N/A**: фильтр блока 4 — «нет»: «это пара сотен строк, работает как всё "
    "приложение»; отдельных требований к скорости и затратам нет."
)


def feature_with(replacements: dict[str, str]) -> str:
    text = (FIXTURES / "customer_feature_good.md").read_text(encoding="utf-8")
    for old, new in replacements.items():
        assert old in text, f"фикстура не содержит {old!r}"
        text = text.replace(old, new)
    return text


def test_full_profile_rejects_na_as_perf_cost_target():
    """Без профиля feature «не применимо» не закрывает GC-20/GC-08 — и это GC-22."""
    text = feature_with({"  profile: feature\n": "", "validation: pass": "validation: fail"})
    rules = {f.rule for f in errors(check(text, base_dir=FIXTURES))}
    assert rules == {"GC-08", "GC-20", "GC-22"}, rules


def test_explicit_full_profile_equals_absent():
    text = customer_with({"  frame: customer\n": "  frame: customer\n  profile: full\n"})
    assert errors(check(text, base_dir=FIXTURES)) == []


@pytest.mark.parametrize("profile", ["short", "[feature]", "Feature"])
def test_unknown_profile_is_gc03(profile):
    text = feature_with({"profile: feature": f"profile: {profile}"})
    refs = [f.ref for f in errors(check(text, base_dir=FIXTURES)) if f.rule == "GC-03"]
    assert refs == ["interview.profile"]


def test_feature_profile_is_customer_only():
    text = (FIXTURES / "engineer_good.md").read_text(encoding="utf-8").replace(
        "  frame: engineer\n", "  frame: engineer\n  profile: feature\n"
    )
    messages = [f.message for f in errors(check(text, base_dir=FIXTURES)) if f.rule == "GC-03"]
    assert messages == ["профиль feature есть только у фрейма customer"]


@pytest.mark.parametrize("placeholder", ["", " —", " -", " не спрашивали", " «»", " « »"])
def test_feature_na_without_reason_is_gc22(placeholder):
    """Причина — цитата ответа заказчика: прочерк и «не спрашивали» её не дают."""
    text = feature_with({NA_NFR: f"**Category**: perf, cost\n**N/A**:{placeholder}"})
    assert gc_errors(text, "GC-22") == ["у **N/A** нет причины словами заказчика в «…»"]
    assert gc_errors(text, "GC-20") != []  # пустая причина цель не закрывает


def test_feature_na_on_fr_is_gc22():
    text = feature_with(
        {"**Acceptance**: повторный экспорт": "**N/A**: «не надо»\n**Acceptance**: повторный экспорт"}
    )
    assert gc_errors(text, "GC-22") == ["**N/A** допустим только у NFR и CON"]


def test_feature_profile_keeps_perf_cost_records_required():
    """«Не применимо» — запись, а не пустота: NFR perf/cost в брифе фичи обязательны."""
    text = feature_with({"**Category**: perf, cost\n": "**Category**: safety\n"})
    assert sorted(gc_errors(text, "GC-20")) == [
        "нет ни одной NFR категории cost",
        "нет ни одной NFR категории perf",
    ]


def test_feature_profile_keeps_translation_and_owner_rules():
    """GC-19/GC-21 под профилем не ослаблены: ответ на фильтр — слова заказчика."""
    text = feature_with(
        {
            "| «там только мои слова» | доказывать | CON-01 | — | — | — |\n": "",
            "`owns: process, data, quality, operations`": "`owns: process, data, operations`",
        }
    )
    assert gc_errors(text, "GC-19") == ["нет ни одной строки категории «доказывать»"]
    assert gc_errors(text, "GC-21") == [
        "владелец не назван: нет P или открытого Q с этим owns"
    ]
