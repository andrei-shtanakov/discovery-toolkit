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
