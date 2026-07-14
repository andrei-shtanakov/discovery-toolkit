"""Пиненая копия контракта в skill-бандле не разъехалась с каноном в корне репо."""

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
CANONICAL = ROOT / "DISCOVERY-BRIEF-CONTRACT.md"
VENDORED = ROOT / ".claude/skills/discovery-interview/contract.md"


def split_pin_header(text: str) -> tuple[str, str]:
    """Копия = заголовок из `>`-строк + пустая строка + канон verbatim."""
    lines = text.splitlines(keepends=True)
    i = 0
    while i < len(lines) and lines[i].startswith(">"):
        i += 1
    assert i > 0, "нет pin-заголовка"
    assert lines[i].strip() == "", "после pin-заголовка нет пустой строки"
    return "".join(lines[:i]), "".join(lines[i + 1 :])


def test_vendored_copy_matches_canonical():
    header, body = split_pin_header(VENDORED.read_text(encoding="utf-8"))
    canonical = CANONICAL.read_text(encoding="utf-8")
    assert body == canonical, "копия контракта в skill разошлась с каноном — обнови её"

    sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    m = re.search(r"sha256:\s*([0-9a-f]{64})", header)
    assert m, "в pin-заголовке нет sha256"
    assert m.group(1) == sha, "sha256 в pin-заголовке не совпадает с каноном — обнови хеш"
