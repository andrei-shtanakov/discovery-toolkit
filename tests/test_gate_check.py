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

@pytest.mark.parametrize("name", ["customer_good.md", "customer_approved.md", "engineer_good.md"])
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
