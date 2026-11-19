"""Банк вопросов фреймов полон относительно coverage-гейта (машинные маркеры тем).

Формат маркера зафиксирован в SKILL.md, «Приложение: маркеры тем банка вопросов».
"""

import re
from pathlib import Path

import pytest

from gate_check import FRAMES

FRAMES_DIR = Path(__file__).parent.parent / ".claude/skills/discovery-interview/frames"

BANK_HEADING = "## Банк вопросов по темам"
_TOPIC_RE = re.compile(r"^###\s+(.*)$")
_MARKER_RE = re.compile(
    r"^<!--\s*coverage_key:\s*([a-z_]+|none);\s*produces:\s*([A-Z,]+|none)\s*-->$"
)

# Префиксы, легальные в `produces`: секции фреймов (contract §2) + инварианты Q/X.
ALLOWED_PREFIXES = {"Q", "X"} | {
    prefix
    for frame in FRAMES.values()
    for group in ("required", "optional")
    for prefix in frame[group].values()
    if prefix
}


def topics(frame: str) -> list[tuple[str, str, list[str]]]:
    """Темы банка вопросов фрейма: (заголовок, coverage_key, produces)."""
    lines = (FRAMES_DIR / f"{frame}.md").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(BANK_HEADING))
    end = next(
        (i for i, line in enumerate(lines[start + 1 :], start + 1) if line.startswith("## ")),
        len(lines),
    )

    result = []
    for i, line in enumerate(lines[start:end], start):
        heading = _TOPIC_RE.match(line)
        if not heading:
            continue
        marker = _MARKER_RE.match(lines[i + 1]) if i + 1 < end else None
        assert marker, f"{frame}: у темы «{heading.group(1)}» нет маркера строкой ниже"
        produces = [] if marker.group(2) == "none" else marker.group(2).split(",")
        result.append((heading.group(1), marker.group(1), produces))
    assert result, f"{frame}: банк вопросов пуст"
    return result


@pytest.mark.parametrize("frame", sorted(FRAMES))
def test_marker_values_are_known(frame):
    """`coverage_key` — ключ этого фрейма или `none`; `produces` — легальные префиксы."""
    keys = set(FRAMES[frame]["required"]) | set(FRAMES[frame]["optional"])
    for heading, key, produces in topics(frame):
        assert key in keys | {"none"}, f"{frame}/«{heading}»: чужой coverage_key {key!r}"
        unknown = set(produces) - ALLOWED_PREFIXES
        assert not unknown, f"{frame}/«{heading}»: неизвестные префиксы {sorted(unknown)}"


@pytest.mark.parametrize("frame", sorted(FRAMES))
def test_every_required_key_has_a_topic(frame):
    """Без темы на required-ключ `gate_passed` по §4 недостижим — банк неполон."""
    claimed = {key for _, key, _ in topics(frame)}
    missing = set(FRAMES[frame]["required"]) - claimed
    assert not missing, f"{frame}: required-ключи без темы в банке: {sorted(missing)}"


@pytest.mark.parametrize("frame", sorted(FRAMES))
def test_every_optional_key_has_a_topic(frame):
    """Optional-ключ без темы недостижим через банк: `partial`/`missing` не дозадать."""
    claimed = {key for _, key, _ in topics(frame)}
    missing = set(FRAMES[frame]["optional"]) - claimed
    assert not missing, f"{frame}: optional-ключи без темы в банке: {sorted(missing)}"


@pytest.mark.parametrize("frame", sorted(FRAMES))
def test_topic_produces_its_section_prefix(frame):
    """Тема ключа с секцией обязана порождать префикс этой секции (банк ⇄ контракт)."""
    sections = {**FRAMES[frame]["required"], **FRAMES[frame]["optional"]}
    for heading, key, produces in topics(frame):
        prefix = sections.get(key)
        if prefix is None:  # ключ-процесс (feasibility_review) или coverage_key: none
            continue
        assert prefix in produces, (
            f"{frame}/«{heading}»: ключ {key} — секция {prefix}, но produces={produces}"
        )


_ID_TEMPLATE_RE = re.compile(r"`[A-Z]+-NN`")


def question_bullets(frame: str) -> list[str]:
    """Пункты-вопросы банка: `- `-строки с продолжениями (как читает runtime)."""
    lines = (FRAMES_DIR / f"{frame}.md").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(BANK_HEADING))
    bullets: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        if line.startswith("- "):
            bullets.append(line[2:])
        elif line.startswith("  ") and line.strip() and bullets:
            bullets[-1] += " " + line.strip()
    return bullets


@pytest.mark.parametrize("frame", sorted(FRAMES))
def test_question_bullets_are_not_composer_instructions(frame):
    """`- ` — вопрос человеку; инструкция составителю (куда писать `X-NN`/`Q-NN`) — `> `.

    Runtime превращает каждый `- `-пункт темы в вопрос стейкхолдеру; шаблон ID в нём
    значит, что составителю адресованное ушло человеку (discovery#71).
    """
    leaked = [b for b in question_bullets(frame) if _ID_TEMPLATE_RE.search(b)]
    assert not leaked, f"{frame}: инструкции под видом вопросов: {leaked}"


# --- профиль feature: короткий набор и вопросы-фильтры (контракт v1.4, issue #35) ---

PROFILE_FRAMES = {"customer"}  # профиль feature есть только у customer (GC-03)
_PROFILE_RE = re.compile(
    r"^<!--\s*profile:\s*feature;\s*short:\s*(none|\d+(?:,\d+)*)"
    r"(?:;\s*filter:\s*([^;]+?))?\s*-->$"
)


def profile_topics(frame: str) -> list[tuple[str, str, int, list[int], str | None]]:
    """Темы с ключом: (заголовок, ключ, число вопросов, short, filter).

    Строка профиля стоит сразу под маркером темы; число вопросов — `- `-пункты темы
    (с продолжениями), как их нумерует runtime.
    """
    lines = (FRAMES_DIR / f"{frame}.md").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(BANK_HEADING))
    result = []
    for i, line in enumerate(lines[start:], start):
        if line.startswith("## ") and i > start:
            break
        marker = _MARKER_RE.match(line)
        if not marker or marker.group(1) == "none":
            continue
        heading = lines[i - 1]
        profile = _PROFILE_RE.match(lines[i + 1])
        assert profile, f"{frame}/{heading}: нет строки профиля под маркером"
        count = 0
        for body in lines[i + 2 :]:
            if body.startswith("#"):
                break
            count += body.startswith("- ")
        short = [] if profile.group(1) == "none" else [int(n) for n in profile.group(1).split(",")]
        result.append((heading, marker.group(1), count, short, profile.group(2)))
    return result


def test_profile_lines_only_in_profile_frames():
    """Строка профиля у фрейма без профиля — разметка, которую никто не прочтёт."""
    for frame in sorted(set(FRAMES) - PROFILE_FRAMES):
        text = (FRAMES_DIR / f"{frame}.md").read_text(encoding="utf-8")
        assert "<!-- profile:" not in text, f"{frame}: профиль feature не для этого фрейма"


@pytest.mark.parametrize("frame", sorted(PROFILE_FRAMES))
def test_short_set_indexes_existing_questions(frame):
    """Номера `short` — позиции `- `-пунктов темы: 1…N, по возрастанию, без повторов."""
    for heading, _, count, short, _ in profile_topics(frame):
        assert short == sorted(set(short)), f"{frame}/{heading}: short={short}"
        assert all(1 <= n <= count for n in short), (
            f"{frame}/{heading}: short={short}, а вопросов {count}"
        )


@pytest.mark.parametrize("frame", sorted(PROFILE_FRAMES))
def test_every_topic_reachable_in_feature_profile(frame):
    """Тема без short и без фильтра в профиле feature молча исчезла бы."""
    for heading, _, _, short, filt in profile_topics(frame):
        assert short or filt, f"{frame}/{heading}: ни short, ни filter"


@pytest.mark.parametrize("frame", sorted(PROFILE_FRAMES))
def test_every_required_key_asked_in_feature_profile(frame):
    """Каждый required-ключ получает в профиле feature хотя бы один вопрос."""
    asked = {key for _, key, _, short, filt in profile_topics(frame) if short or filt}
    missing = set(FRAMES[frame]["required"]) - asked
    assert not missing, f"{frame}: в профиле feature ключи без вопросов: {sorted(missing)}"


@pytest.mark.parametrize("frame", sorted(PROFILE_FRAMES))
def test_filters_are_questions_to_a_human(frame):
    """Фильтр задаётся человеку как есть: вопрос, без шаблонов ID составителю."""
    for heading, _, _, _, filt in profile_topics(frame):
        if filt is None:
            continue
        assert filt.endswith("?"), f"{frame}/{heading}: фильтр не вопрос: {filt!r}"
        assert not _ID_TEMPLATE_RE.search(filt), f"{frame}/{heading}: {filt!r}"


def test_customer_short_set_is_short():
    """Смысл профиля — длина: короткий набор (с фильтрами) не больше трети банка."""
    rows = profile_topics("customer")
    full = sum(count for _, _, count, _, _ in rows)
    short = sum(len(s) + (f is not None) for _, _, _, s, f in rows)
    assert short * 3 <= full, f"короткий набор {short} из {full}"
