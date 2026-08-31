#!/usr/bin/env python3
"""Validate canonical Living PRD structure, traceability, links, and safety."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from prd_progress import (
    ACTION_ID_RE,
    CHANGELOG_MARKER,
    CHANGELOG_VARIANTS,
    DEPENDENCY_HEADERS_LEGACY_ZH,
    DEPENDENCY_MARKER,
    DEPENDENCY_VARIANTS,
    FUNCTIONAL_MARKER,
    NEXT_END,
    NEXT_HEADERS_EN,
    NEXT_HEADERS_LEGACY_ZH,
    NEXT_HEADERS_ZH,
    NEXT_START,
    PROGRESS_HEADERS_LEGACY_ZH,
    PROGRESS_VARIANTS,
    REQUIREMENT_ID_RE,
    SECRET_PATTERNS,
    TECHNICAL_MARKER,
    TRACKED_ID_RE,
    UpdateError,
    cell,
    dcols,
    find_table,
    find_version,
    parse_md_row,
    pcols,
    version_text,
)


TRACEABILITY_MARKER = "<!-- PRD-LIFECYCLE:TRACEABILITY -->"
TRACE_HEADERS_EN = [
    "Requirement ID", "User Story / Use Case", "Acceptance Criteria", "Analytics",
    "Dependencies", "Source / Evidence Class",
]
TRACE_HEADERS_ZH = ["需求 ID", "用户故事 / 用例", "验收标准", "分析事件", "依赖", "来源 / 证据分类"]
INTERNAL_IP_RE = re.compile(
    r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"
)
RANGE_ID_RE = re.compile(r"\b((?:Q|R|C|FR|TR|NFR)-[A-Z0-9-]*\d{3})\s*[–—]\s*((?:Q|R|C|FR|TR|NFR)-)?\d{3}\b")
RELATIVE_LINK_RE = re.compile(r"\]\((\./[^)#]+)")
USER_STORY_RE = re.compile(r"\bUS(?:-[A-Z0-9]+)+-\d{3}\b")
USE_CASE_RE = re.compile(r"\bUC(?:-[A-Z0-9]+)+-\d{3}\b")
AC_RE = re.compile(r"\bAC(?:-[A-Z0-9]+)+-\d{3}\b")
NFR_RE = re.compile(r"\bNFR(?:-[A-Z0-9]+)*-\d{3}\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prd", help="Canonical Markdown PRD")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as validation failures")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output")
    return parser.parse_args()


def validate(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return [f"File not found: {path}"], warnings
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ["PRD must be valid UTF-8"], warnings
    lines = text.splitlines()

    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            errors.append("Possible credential or secret found; redact it before delivery")
            break
    if INTERNAL_IP_RE.search(text):
        errors.append("Internal network address found; remove or redact it from the product PRD")
    if RANGE_ID_RE.search(text):
        errors.append("Tracked IDs must be individual rows; ranges such as Q-001–Q-010 are not allowed")

    try:
        _index, version, _match = find_version(lines)
        version_string = version_text(version)
        filename_match = re.search(r"_v(\d+\.\d+\.\d+)\.md$", path.name, re.I)
        if filename_match and version_string != f"v{filename_match.group(1)}":
            errors.append(f"Filename version and document version differ: {path.name} vs {version_string}")
    except UpdateError as exc:
        errors.append(str(exc))

    progress_tables = []
    for marker in (FUNCTIONAL_MARKER, TECHNICAL_MARKER):
        try:
            table = find_table(lines, marker, PROGRESS_VARIANTS)
            progress_tables.append(table)
            if table.headers == PROGRESS_HEADERS_LEGACY_ZH:
                warnings.append(f"{marker} uses the legacy progress schema without Status Basis")
        except UpdateError as exc:
            errors.append(str(exc))

    dependency_table = None
    try:
        dependency_table = find_table(lines, DEPENDENCY_MARKER, DEPENDENCY_VARIANTS)
        if dependency_table.headers == DEPENDENCY_HEADERS_LEGACY_ZH:
            warnings.append("Dependency register uses the legacy schema without Hard/Soft/Gate classification")
    except UpdateError as exc:
        errors.append(str(exc))

    try:
        find_table(lines, CHANGELOG_MARKER, CHANGELOG_VARIANTS)
    except UpdateError as exc:
        errors.append(str(exc))

    requirement_rows: dict[str, tuple[list[str], dict[str, int | None]]] = {}
    p0_functional: set[str] = set()
    for table_index, table in enumerate(progress_tables):
        cols = pcols(table.headers)
        for row in table.rows:
            requirement_id = cell(row, cols["id"])
            if not REQUIREMENT_ID_RE.fullmatch(requirement_id):
                errors.append(f"Invalid individual requirement ID: {requirement_id}")
                continue
            if requirement_id in requirement_rows:
                errors.append(f"Duplicate requirement ID: {requirement_id}")
                continue
            requirement_rows[requirement_id] = (row, cols)
            status = cell(row, cols["status"])
            basis = cell(row, cols["basis"])
            dependencies = cell(row, cols["dependencies"])
            notes = cell(row, cols["notes"])
            completion_date = cell(row, cols["date"])
            if cols["basis"] is not None and basis in {"", "—", "-"}:
                errors.append(f"{requirement_id} is missing Status Basis")
            if status in {"Reported Complete", "Verified"} and completion_date in {"", "—", "-"}:
                errors.append(f"{requirement_id} requires a completion date for {status}")
            if status == "Verified" and notes in {"", "—", "-"}:
                errors.append(f"{requirement_id} is Verified without recorded evidence")
            if status == "Blocked" and dependencies in {"", "—", "-"}:
                errors.append(f"{requirement_id} is Blocked without a dependency")
            if table_index == 0 and cell(row, cols["priority"]) == "P0":
                p0_functional.add(requirement_id)

    dependencies: dict[str, dict[str, str]] = {}
    if dependency_table:
        cols = dcols(dependency_table.headers)
        for row in dependency_table.rows:
            dependency_id = cell(row, cols["id"])
            if not re.fullmatch(r"(?:Q|R|C)(?:-[A-Z0-9]+)*-\d{3}", dependency_id):
                errors.append(f"Dependency rows require one individual Q/R/C ID: {dependency_id}")
                continue
            if dependency_id in dependencies or dependency_id in requirement_rows:
                errors.append(f"Duplicate tracked ID: {dependency_id}")
                continue
            level = cell(row, cols["level"], "Hard")
            dependencies[dependency_id] = {"level": level, "status": cell(row, cols["status"])}
            if cols["level"] is not None and level not in {"Hard", "Soft", "Gate"}:
                errors.append(f"Invalid blocking level for {dependency_id}: {level}")

    known_ids = set(requirement_rows) | set(dependencies)
    for requirement_id, (row, cols) in requirement_rows.items():
        dependency_text = cell(row, cols["dependencies"])
        for dependency_id in TRACKED_ID_RE.findall(dependency_text):
            if dependency_id not in known_ids:
                errors.append(f"{requirement_id} references unknown dependency {dependency_id}")
        if cell(row, cols["status"]) == "Blocked":
            found = [dependencies.get(item) for item in TRACKED_ID_RE.findall(dependency_text)]
            if found and all(info and info["level"] == "Soft" for info in found):
                errors.append(f"{requirement_id} is Blocked only by Soft dependencies")

    try:
        start = lines.index(NEXT_START)
        end = lines.index(NEXT_END, start + 1)
        action_lines = [line for line in lines[start + 1 : end] if line.strip()]
        if len(action_lines) < 2:
            errors.append("Current Action Snapshot is missing its table")
        else:
            headers = parse_md_row(action_lines[0])
            if headers == NEXT_HEADERS_LEGACY_ZH:
                warnings.append("Current Action Snapshot uses legacy IDs; stable A-* and Target ID columns are required")
            elif headers not in (NEXT_HEADERS_EN, NEXT_HEADERS_ZH):
                errors.append(f"Unexpected Current Action Snapshot headers: {headers}")
            else:
                action_ids: set[str] = set()
                for line in action_lines[2:]:
                    if not line.strip().startswith("|"):
                        continue
                    row = parse_md_row(line)
                    if row[0] == "—":
                        continue
                    if not ACTION_ID_RE.fullmatch(row[0]):
                        errors.append(f"Invalid Action ID: {row[0]}")
                    elif row[0] in action_ids:
                        errors.append(f"Duplicate Action ID: {row[0]}")
                    action_ids.add(row[0])
                    if row[1] not in known_ids:
                        errors.append(f"{row[0]} references unknown Target ID {row[1]}")
    except ValueError:
        errors.append("Missing Current Action Snapshot markers")

    story_ids = set(USER_STORY_RE.findall(text))
    use_case_ids = set(USE_CASE_RE.findall(text))
    if not story_ids:
        errors.append("At least one stable US-* user story is required")
    if not use_case_ids:
        errors.append("At least one stable UC-* use case is required")
    if not NFR_RE.search(text):
        warnings.append("No stable NFR-* requirement found; explain why NFRs are inapplicable or add them")

    trace_rows: dict[str, list[str]] = {}
    try:
        trace_table = find_table(lines, TRACEABILITY_MARKER, [TRACE_HEADERS_EN, TRACE_HEADERS_ZH])
        for row in trace_table.rows:
            requirement_id = row[0]
            if requirement_id in trace_rows:
                errors.append(f"Duplicate traceability row for {requirement_id}")
            trace_rows[requirement_id] = row
    except UpdateError as exc:
        errors.append(str(exc))

    for requirement_id in sorted(p0_functional):
        row = trace_rows.get(requirement_id)
        if not row:
            errors.append(f"P0 requirement {requirement_id} is missing from traceability")
            continue
        if not (USER_STORY_RE.search(row[1]) or USE_CASE_RE.search(row[1])):
            errors.append(f"P0 requirement {requirement_id} lacks a US-* or UC-* mapping")
        if not AC_RE.search(row[2]):
            errors.append(f"P0 requirement {requirement_id} lacks an AC-* mapping")

    for link in RELATIVE_LINK_RE.findall(text):
        target = (path.parent / link).resolve()
        if not target.exists():
            errors.append(f"Broken relative link: {link}")

    return errors, warnings


def main() -> int:
    args = parse_args()
    path = Path(args.prd).resolve()
    errors, warnings = validate(path)
    failed = bool(errors or (args.strict and warnings))
    result = {"file": str(path), "valid": not failed, "errors": errors, "warnings": warnings}
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"{'VALID' if not failed else 'INVALID'}: {path}")
        for item in errors:
            print(f"ERROR: {item}")
        for item in warnings:
            print(f"WARNING: {item}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
