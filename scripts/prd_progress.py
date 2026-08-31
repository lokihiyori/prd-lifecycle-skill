#!/usr/bin/env python3
"""Deterministically update canonical Living PRD progress and decisions."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FUNCTIONAL_MARKER = "<!-- PRD-LIFECYCLE:FUNCTIONAL-PROGRESS -->"
TECHNICAL_MARKER = "<!-- PRD-LIFECYCLE:TECHNICAL-PROGRESS -->"
DEPENDENCY_MARKER = "<!-- PRD-LIFECYCLE:DEPENDENCY-REGISTER -->"
NEXT_START = "<!-- PRD-LIFECYCLE:NEXT-STEPS:START -->"
NEXT_END = "<!-- PRD-LIFECYCLE:NEXT-STEPS:END -->"
CHANGELOG_MARKER = "<!-- PRD-LIFECYCLE:CHANGELOG -->"

PROGRESS_HEADERS_EN = [
    "ID", "Requirement", "Priority", "Delivery Status", "Status Basis", "Owner",
    "Completion Date", "Dependencies", "Notes / Evidence",
]
PROGRESS_HEADERS_ZH = [
    "ID", "需求项", "优先级", "交付状态", "状态依据", "负责人", "完成日期", "依赖", "备注/证据",
]
PROGRESS_HEADERS_LEGACY_ZH = ["ID", "需求项", "优先级", "状态", "负责人", "完成日期", "依赖", "备注/证据"]

DEPENDENCY_HEADERS_EN = [
    "ID", "Type", "Blocking Level", "Item", "Status", "Affects", "Owner", "Due Date", "Notes / Evidence",
]
DEPENDENCY_HEADERS_ZH = [
    "ID", "类型", "阻塞级别", "事项", "状态", "影响项", "负责人", "截止日期", "备注/证据",
]
DEPENDENCY_HEADERS_LEGACY_ZH = ["ID", "类型", "事项", "状态", "负责人", "截止日期", "备注/证据"]

NEXT_HEADERS_EN = [
    "Action ID", "Target ID", "Recommended Action", "Reason", "Suggested Owner", "Target Date", "Completion Evidence",
]
NEXT_HEADERS_ZH = ["Action ID", "Target ID", "推荐动作", "原因", "建议负责人", "目标日期", "完成证据"]
NEXT_HEADERS_LEGACY_ZH = ["ID", "推荐动作", "原因", "建议负责人", "目标日期", "完成证据"]

CHANGELOG_HEADERS_EN = ["Version", "Date", "Updated By", "Change", "Evidence"]
CHANGELOG_HEADERS_ZH = ["版本", "日期", "更新人", "变更内容", "证据"]

PROGRESS_VARIANTS = [PROGRESS_HEADERS_EN, PROGRESS_HEADERS_ZH, PROGRESS_HEADERS_LEGACY_ZH]
DEPENDENCY_VARIANTS = [DEPENDENCY_HEADERS_EN, DEPENDENCY_HEADERS_ZH, DEPENDENCY_HEADERS_LEGACY_ZH]
CHANGELOG_VARIANTS = [CHANGELOG_HEADERS_EN, CHANGELOG_HEADERS_ZH]

ALLOWED_STATUSES = {"Not Started", "In Progress", "Blocked", "Reported Complete", "Verified"}
STATUS_ALIASES = {
    "未开始": "Not Started", "进行中": "In Progress", "阻塞": "Blocked",
    "已完成": "Reported Complete", "已报告完成": "Reported Complete", "已验证": "Verified",
}
DEPENDENCY_STATUSES = {"Open", "In Progress", "Resolved"}
DEPENDENCY_STATUS_ALIASES = {"未解决": "Open", "进行中": "In Progress", "已解决": "Resolved", "关闭": "Resolved"}
BLOCKING_LEVELS = {"Hard", "Soft", "Gate"}
PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2}
STATUS_RANK = {"Reported Complete": 0, "In Progress": 1, "Not Started": 2}

TRACKED_ID_RE = re.compile(r"\b(?:FR|TR|NFR|Q|R|C)(?:-[A-Z0-9]+)*-\d{3}\b")
REQUIREMENT_ID_RE = re.compile(r"^(?:FR|TR|NFR)(?:-[A-Z0-9]+)*-\d{3}$")
DEPENDENCY_ID_RE = re.compile(r"^(?:Q|R|C)(?:-[A-Z0-9]+)*-\d{3}$")
ACTION_ID_RE = re.compile(r"^A-(\d{3})$")
VERSION_PATTERNS = [
    re.compile(r"^(\|\s*PRD Version\s*\|\s*)v(\d+)\.(\d+)\.(\d+)(\s*\|.*)$", re.I),
    re.compile(r"^(\|\s*PRD 文档版本\s*\|\s*)v(\d+)\.(\d+)\.(\d+)(\s*\|.*)$"),
]
SECRET_PATTERNS = [
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"(?i)\b(?:password|passwd|secret|token|api[_ -]?key|maintenance[_ -]?key)\s*[:=]\s*[^\s,;]{6,}"),
]


class UpdateError(ValueError):
    pass


@dataclass
class Table:
    header_index: int
    end_index: int
    headers: list[str]
    rows: list[list[str]]


def parse_md_row(line: str) -> list[str]:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        raise UpdateError(f"Invalid Markdown table row: {line}")
    return [cell.replace("\\|", "|").strip() for cell in re.split(r"(?<!\\)\|", stripped[1:-1])]


def sanitize_cell(value: Any) -> str:
    return str(value).replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>").strip()


def render_md_row(cells: list[str]) -> str:
    safe = [sanitize_cell(cell).replace("|", "\\|") or "—" for cell in cells]
    return "| " + " | ".join(safe) + " |"


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def find_table(lines: list[str], marker: str, variants: list[list[str]]) -> Table:
    try:
        marker_index = lines.index(marker)
    except ValueError as exc:
        raise UpdateError(f"Missing required marker: {marker}") from exc
    header_index = marker_index + 1
    while header_index < len(lines) and not lines[header_index].strip():
        header_index += 1
    if header_index + 1 >= len(lines):
        raise UpdateError(f"Missing table after marker: {marker}")
    headers = parse_md_row(lines[header_index])
    if headers not in variants:
        raise UpdateError(f"Unexpected headers after {marker}: {headers}")
    separator = parse_md_row(lines[header_index + 1])
    if len(separator) != len(headers) or not is_separator(separator):
        raise UpdateError(f"Invalid table separator after marker: {marker}")
    row_index = header_index + 2
    rows: list[list[str]] = []
    while row_index < len(lines) and lines[row_index].strip().startswith("|"):
        row = parse_md_row(lines[row_index])
        if len(row) != len(headers):
            raise UpdateError(f"Wrong column count near line {row_index + 1}")
        rows.append(row)
        row_index += 1
    return Table(header_index, row_index, headers, rows)


def header_index(headers: list[str], *names: str) -> int | None:
    for name in names:
        if name in headers:
            return headers.index(name)
    return None


def pcols(headers: list[str]) -> dict[str, int | None]:
    return {
        "id": header_index(headers, "ID"),
        "title": header_index(headers, "Requirement", "需求项"),
        "priority": header_index(headers, "Priority", "优先级"),
        "status": header_index(headers, "Delivery Status", "交付状态", "状态"),
        "basis": header_index(headers, "Status Basis", "状态依据"),
        "owner": header_index(headers, "Owner", "负责人"),
        "date": header_index(headers, "Completion Date", "完成日期"),
        "dependencies": header_index(headers, "Dependencies", "依赖"),
        "notes": header_index(headers, "Notes / Evidence", "备注/证据"),
    }


def dcols(headers: list[str]) -> dict[str, int | None]:
    return {
        "id": header_index(headers, "ID"), "type": header_index(headers, "Type", "类型"),
        "level": header_index(headers, "Blocking Level", "阻塞级别"),
        "item": header_index(headers, "Item", "事项"), "status": header_index(headers, "Status", "状态"),
        "affects": header_index(headers, "Affects", "影响项"), "owner": header_index(headers, "Owner", "负责人"),
        "date": header_index(headers, "Due Date", "截止日期"),
        "notes": header_index(headers, "Notes / Evidence", "备注/证据"),
    }


def cell(row: list[str], index: int | None, default: str = "—") -> str:
    return row[index] if index is not None else default


def set_cell(row: list[str], index: int | None, value: Any) -> None:
    if index is not None:
        row[index] = sanitize_cell(value) or "—"


def normalize_status(value: str) -> str:
    status = STATUS_ALIASES.get(value.strip(), value.strip())
    if status not in ALLOWED_STATUSES:
        raise UpdateError(f"Unsupported delivery status: {value}")
    return status


def normalize_dependency_status(value: str) -> str:
    status = DEPENDENCY_STATUS_ALIASES.get(value.strip(), value.strip())
    if status not in DEPENDENCY_STATUSES:
        raise UpdateError(f"Unsupported dependency status: {value}")
    return status


def validate_iso_date(value: str) -> str:
    try:
        return dt.date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise UpdateError(f"Invalid ISO date: {value}") from exc


def append_note(existing: str, addition: str) -> str:
    addition = sanitize_cell(addition)
    if not addition:
        return existing
    if existing in {"", "—", "-"}:
        return addition
    if addition in existing:
        return existing
    return f"{existing}；{addition}"


def flatten_evidence(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(sanitize_cell(item) for item in value if sanitize_cell(item))
    return sanitize_cell(value)


def reject_secrets(value: Any) -> None:
    serialized = json.dumps(value, ensure_ascii=False)
    for pattern in SECRET_PATTERNS:
        if pattern.search(serialized):
            raise UpdateError("Update appears to contain a credential or secret; redact it before updating the PRD")


def normalize_title(value: str) -> str:
    return re.sub(r"[\s\-—_：:（）()]+", "", value).casefold()


def resolve_progress_row(
    update: dict[str, Any], rows_by_id: dict[str, tuple[list[str], dict[str, int | None]]], rows: list[tuple[list[str], dict[str, int | None]]]
) -> tuple[str, list[str], dict[str, int | None]]:
    raw_id = update.get("id")
    if raw_id:
        requirement_id = sanitize_cell(raw_id)
        found = rows_by_id.get(requirement_id)
        if found is None:
            raise UpdateError(f"Unknown requirement ID: {requirement_id}")
        return requirement_id, found[0], found[1]
    raw_title = update.get("title")
    if not raw_title:
        raise UpdateError("Each progress update must contain an 'id' or unique 'title'")
    target = normalize_title(str(raw_title))
    exact = [(row, cols) for row, cols in rows if normalize_title(cell(row, cols["title"])) == target]
    if len(exact) == 1:
        row, cols = exact[0]
        return cell(row, cols["id"]), row, cols
    partial = [
        (row, cols) for row, cols in rows
        if target in normalize_title(cell(row, cols["title"])) or normalize_title(cell(row, cols["title"])) in target
    ]
    if len(partial) == 1:
        row, cols = partial[0]
        return cell(row, cols["id"]), row, cols
    candidates = ", ".join(cell(row, cols["id"]) for row, cols in (exact or partial)) or "none"
    raise UpdateError(f"Ambiguous or unmatched requirement title '{raw_title}'; candidates: {candidates}")


def find_version(lines: list[str]) -> tuple[int, tuple[int, int, int], re.Match[str]]:
    for index, line in enumerate(lines):
        for pattern in VERSION_PATTERNS:
            match = pattern.match(line)
            if match:
                return index, tuple(int(match.group(i)) for i in (2, 3, 4)), match
    raise UpdateError("Could not find a '| PRD Version | vX.Y.Z |' or Chinese equivalent row")


def version_text(version: tuple[int, int, int]) -> str:
    return "v" + ".".join(map(str, version))


def bump_version(version: tuple[int, int, int], bump: str) -> tuple[int, int, int]:
    major, minor, patch = version
    if bump == "major":
        return major + 1, 0, 0
    if bump == "minor":
        return major, minor + 1, 0
    return major, minor, patch + 1


def update_version(lines: list[str], bump: str, explicit: str | None, required_bump: str) -> tuple[str, str]:
    index, old_tuple, match = find_version(lines)
    rank = {"patch": 0, "minor": 1, "major": 2}
    effective_bump = required_bump if bump == "auto" else bump
    if rank[effective_bump] < rank[required_bump]:
        raise UpdateError(f"This update requires at least a {required_bump} version bump")
    if explicit:
        explicit_match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", explicit.strip())
        if not explicit_match:
            raise UpdateError(f"Invalid explicit version: {explicit}")
        new_tuple = tuple(int(explicit_match.group(i)) for i in (1, 2, 3))
        if new_tuple <= old_tuple:
            raise UpdateError("New version must be greater than the current version")
    else:
        new_tuple = bump_version(old_tuple, effective_bump)
    lines[index] = f"{match.group(1)}{version_text(new_tuple)}{match.group(5)}"
    return version_text(old_tuple), version_text(new_tuple)


def render_table(table: Table) -> list[str]:
    rendered = [render_md_row(table.headers), "|" + "---|" * len(table.headers)]
    rendered.extend(render_md_row(row) for row in table.rows)
    return rendered


def parse_existing_actions(lines: list[str]) -> tuple[dict[str, str], int]:
    try:
        start = lines.index(NEXT_START)
        end = lines.index(NEXT_END, start + 1)
    except ValueError as exc:
        raise UpdateError("Missing next-step marker block") from exc
    block = [line for line in lines[start + 1 : end] if line.strip()]
    mapping: dict[str, str] = {}
    max_id = 0
    if len(block) < 2:
        return mapping, max_id
    headers = parse_md_row(block[0])
    for line in block[2:]:
        if not line.strip().startswith("|"):
            continue
        row = parse_md_row(line)
        if len(row) != len(headers):
            continue
        first = row[0]
        action_match = ACTION_ID_RE.fullmatch(first)
        if action_match:
            max_id = max(max_id, int(action_match.group(1)))
        target = ""
        if headers in (NEXT_HEADERS_EN, NEXT_HEADERS_ZH):
            target = row[1]
        elif headers == NEXT_HEADERS_LEGACY_ZH:
            if not action_match and TRACKED_ID_RE.fullmatch(first):
                target = first
            else:
                ids = TRACKED_ID_RE.findall(" ".join(row[1:]))
                target = ids[0] if ids else ""
        if action_match and target:
            mapping[target] = first
    return mapping, max_id


def dependency_info(table: Table) -> dict[str, dict[str, str]]:
    cols = dcols(table.headers)
    result: dict[str, dict[str, str]] = {}
    for row in table.rows:
        dependency_id = cell(row, cols["id"])
        if not DEPENDENCY_ID_RE.fullmatch(dependency_id):
            raise UpdateError(f"Dependency rows require one individual Q/R/C ID, found: {dependency_id}")
        if dependency_id in result:
            raise UpdateError(f"Duplicate dependency ID: {dependency_id}")
        level = cell(row, cols["level"], "Hard")
        if level in {"—", "-", ""}:
            level = "Hard"
        if level not in BLOCKING_LEVELS:
            raise UpdateError(f"Unsupported blocking level for {dependency_id}: {level}")
        result[dependency_id] = {
            "type": cell(row, cols["type"]), "level": level, "item": cell(row, cols["item"]),
            "status": cell(row, cols["status"]), "affects": cell(row, cols["affects"]),
            "owner": cell(row, cols["owner"]), "date": cell(row, cols["date"]), "notes": cell(row, cols["notes"]),
        }
    return result


def unresolved_dependencies(
    dependency_text: str,
    rows_by_id: dict[str, tuple[list[str], dict[str, int | None]]],
    dependencies: dict[str, dict[str, str]],
) -> list[str]:
    normalized = dependency_text.strip()
    if normalized in {"", "—", "-", "无", "None", "none"}:
        return []
    ids = TRACKED_ID_RE.findall(normalized)
    if not ids:
        return [normalized]
    unresolved: list[str] = []
    for dependency_id in ids:
        requirement = rows_by_id.get(dependency_id)
        if requirement:
            row, cols = requirement
            if cell(row, cols["status"]) != "Verified":
                unresolved.append(dependency_id)
            continue
        registered = dependencies.get(dependency_id)
        if registered:
            if registered["status"] != "Resolved" and registered["level"] in {"Hard", "Gate"}:
                unresolved.append(dependency_id)
            continue
        unresolved.append(dependency_id)
    return unresolved


def build_recommendations(
    ordered_rows: list[tuple[list[str], dict[str, int | None]]],
    rows_by_id: dict[str, tuple[list[str], dict[str, int | None]]],
    dependencies: dict[str, dict[str, str]],
    limit: int,
) -> list[dict[str, str]]:
    blocked_by: dict[str, dict[str, Any]] = {}
    normal: list[tuple[int, int, int, int, dict[str, str]]] = []
    downstream: dict[str, int] = {}
    for row, cols in ordered_rows:
        for dependency_id in TRACKED_ID_RE.findall(cell(row, cols["dependencies"])):
            downstream[dependency_id] = downstream.get(dependency_id, 0) + 1

    for order, (row, cols) in enumerate(ordered_rows):
        requirement_id = cell(row, cols["id"])
        title = cell(row, cols["title"])
        priority = cell(row, cols["priority"])
        status = cell(row, cols["status"])
        blockers = unresolved_dependencies(cell(row, cols["dependencies"]), rows_by_id, dependencies)
        if status == "Blocked" and not blockers:
            blockers = [requirement_id]
        if blockers:
            for blocker in blockers:
                if blocker in rows_by_id:
                    continue
                entry = blocked_by.setdefault(blocker, {
                    "priority": PRIORITY_RANK.get(priority, 99), "order": order, "requirements": [],
                })
                entry["priority"] = min(entry["priority"], PRIORITY_RANK.get(priority, 99))
                entry["order"] = min(entry["order"], order)
                entry["requirements"].append(requirement_id)
            continue
        if status not in STATUS_RANK:
            continue
        if status == "Reported Complete":
            action = f"Verify {title}"
            reason = f"{priority}; reported complete and ready for acceptance-evidence review"
            expected = "Evidence mapped to the acceptance criteria"
        elif status == "In Progress":
            action = f"Continue {title}"
            reason = f"{priority}; in progress with no unresolved Hard/Gate dependency"
            expected = "Next explicit checkpoint deliverable"
        else:
            action = f"Start {title}"
            reason = f"{priority}; not started with no unresolved Hard/Gate dependency"
            expected = "First verifiable deliverable"
        owner = cell(row, cols["owner"])
        candidate = {
            "target": requirement_id, "action": action, "reason": reason,
            "owner": owner if owner not in {"", "—", "-"} else "Requirement owner",
            "date": "Owner to schedule", "evidence": expected,
        }
        normal.append((PRIORITY_RANK.get(priority, 99), STATUS_RANK[status], -downstream.get(requirement_id, 0), order, candidate))

    candidates: list[tuple[int, int, int, int, dict[str, str]]] = normal
    for blocker, entry in blocked_by.items():
        info = dependencies.get(blocker)
        affected = sorted(set(entry["requirements"]))
        affected_text = ", ".join(affected[:4]) + (f" and {len(affected) - 4} more" if len(affected) > 4 else "")
        if info:
            candidate = {
                "target": blocker, "action": f"Resolve {info['item']}",
                "reason": f"{info['level']} dependency blocking {len(affected)} item(s): {affected_text}",
                "owner": info["owner"] if info["owner"] not in {"", "—", "-"} else "Dependency owner",
                "date": info["date"] if info["date"] not in {"", "—", "-"} else "Before next review",
                "evidence": info["notes"] if info["notes"] not in {"", "—", "-"} else "Approved decision or closure evidence",
            }
        elif blocker in affected:
            candidate = {
                "target": blocker, "action": f"Clarify the blocker for {blocker}",
                "reason": "Item is Blocked without a recorded dependency", "owner": "Requirement owner",
                "date": "Before next review", "evidence": "Numbered dependency or unblock record",
            }
        else:
            candidate = {
                "target": blocker, "action": f"Confirm and resolve {blocker}",
                "reason": f"Unregistered dependency blocking {len(affected)} item(s): {affected_text}",
                "owner": "Dependency owner", "date": "Before next review", "evidence": "Dependency resolution record",
            }
        candidates.append((entry["priority"], -1, -len(affected), entry["order"], candidate))

    candidates.sort(key=lambda item: item[:4])
    return [item[4] for item in candidates[: max(limit, 0)]]


def replace_next_steps(lines: list[str], recommendations: list[dict[str, str]], prefer_english: bool) -> list[str]:
    try:
        start = lines.index(NEXT_START)
        end = lines.index(NEXT_END, start + 1)
    except ValueError as exc:
        raise UpdateError("Missing next-step marker block") from exc
    existing, max_action_id = parse_existing_actions(lines)
    headers = NEXT_HEADERS_EN if prefer_english else NEXT_HEADERS_ZH
    block = [NEXT_START, render_md_row(headers), "|" + "---|" * len(headers)]
    for recommendation in recommendations:
        target = recommendation["target"]
        action_id = existing.get(target)
        if not action_id:
            max_action_id += 1
            action_id = f"A-{max_action_id:03d}"
        block.append(render_md_row([
            action_id, target, recommendation["action"], recommendation["reason"],
            recommendation["owner"], recommendation["date"], recommendation["evidence"],
        ]))
    if not recommendations:
        block.append(render_md_row(["—", "—", "No current unfinished action", "All tracked work is Verified", "—", "—", "—"]))
    block.append(NEXT_END)
    lines[start : end + 1] = block
    return [row.split(" | ")[1] if " | " in row else row for row in block[3:-1]]


def insert_changelog(lines: list[str], version: str, date: str, actor: str, changes: list[dict[str, str]], evidence: str) -> None:
    table = find_table(lines, CHANGELOG_MARKER, CHANGELOG_VARIANTS)
    summary = "; ".join(f"{item['id']}: {item['old']}→{item['new']}" for item in changes)
    row = render_md_row([version, date, actor, summary, evidence or "—"])
    lines.insert(table.header_index + 2, row)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prd", required=True, help="Input canonical Markdown PRD")
    parser.add_argument("--updates", required=True, help="JSON file containing updates and/or dependency_updates")
    parser.add_argument("--output", required=True, help="New versioned Markdown path; must differ from input")
    parser.add_argument("--actor", required=True, help="Person or stable employee identifier")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="ISO change date")
    parser.add_argument("--bump", choices=("auto", "patch", "minor", "major"), default="auto")
    parser.add_argument("--new-version", help="Explicit vX.Y.Z override; must increase")
    parser.add_argument("--expected-version", help="Abort unless the input has this vX.Y.Z version")
    parser.add_argument("--expected-sha256", help="Abort unless the input SHA-256 matches")
    parser.add_argument("--recommend-limit", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    change_date = validate_iso_date(args.date)
    input_path = Path(args.prd).resolve()
    output_path = Path(args.output).resolve()
    if input_path == output_path:
        raise UpdateError("Refusing to overwrite the input; provide a new versioned output path")
    if not input_path.is_file():
        raise UpdateError(f"Input PRD not found: {input_path}")
    if not output_path.parent.is_dir():
        raise UpdateError(f"Output directory does not exist: {output_path.parent}")
    raw = input_path.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if args.expected_sha256 and actual_sha.lower() != args.expected_sha256.lower():
        raise UpdateError("Input SHA-256 changed; reload and reconcile the authoritative PRD")

    payload = json.loads(Path(args.updates).read_text(encoding="utf-8"))
    reject_secrets(payload)
    updates = payload.get("updates", [])
    dependency_updates = payload.get("dependency_updates", [])
    unapplied = payload.get("unapplied", [])
    if not isinstance(updates, list) or not isinstance(dependency_updates, list) or not isinstance(unapplied, list):
        raise UpdateError("'updates', 'dependency_updates', and 'unapplied' must be arrays")
    if not updates and not dependency_updates:
        raise UpdateError("Updates JSON must contain at least one update")

    lines = raw.decode("utf-8").splitlines()
    _version_index, current_version, _match = find_version(lines)
    if args.expected_version and version_text(current_version) != (args.expected_version if args.expected_version.startswith("v") else f"v{args.expected_version}"):
        raise UpdateError("Input version changed; reload and reconcile the authoritative PRD")

    progress_tables = [find_table(lines, FUNCTIONAL_MARKER, PROGRESS_VARIANTS), find_table(lines, TECHNICAL_MARKER, PROGRESS_VARIANTS)]
    dependency_table = find_table(lines, DEPENDENCY_MARKER, DEPENDENCY_VARIANTS)
    rows_by_id: dict[str, tuple[list[str], dict[str, int | None]]] = {}
    ordered_rows: list[tuple[list[str], dict[str, int | None]]] = []
    for table in progress_tables:
        cols = pcols(table.headers)
        for row in table.rows:
            requirement_id = cell(row, cols["id"])
            if not REQUIREMENT_ID_RE.fullmatch(requirement_id):
                raise UpdateError(f"Invalid individual requirement ID: {requirement_id}")
            if requirement_id in rows_by_id:
                raise UpdateError(f"Duplicate requirement ID: {requirement_id}")
            if cell(row, cols["priority"]) not in PRIORITY_RANK:
                raise UpdateError(f"Unsupported priority for {requirement_id}: {cell(row, cols['priority'])}")
            normalize_status(cell(row, cols["status"]))
            rows_by_id[requirement_id] = (row, cols)
            ordered_rows.append((row, cols))

    dependencies = dependency_info(dependency_table)
    requested: set[str] = set()
    transitions: list[dict[str, str]] = []
    evidence_items: list[str] = []
    semantic_change = False

    for update in updates:
        if not isinstance(update, dict):
            raise UpdateError("Each progress update must be an object")
        requirement_id, row, cols = resolve_progress_row(update, rows_by_id, ordered_rows)
        if requirement_id in requested:
            raise UpdateError(f"Duplicate update ID: {requirement_id}")
        requested.add(requirement_id)
        before = list(row)
        old_status = cell(row, cols["status"])
        new_status = normalize_status(str(update.get("status", old_status)))
        evidence = flatten_evidence(update.get("evidence"))
        if new_status == "Verified" and (update.get("verification_confirmed") is not True or not evidence):
            raise UpdateError(f"{requirement_id} cannot become Verified without evidence and verification_confirmed=true")
        set_cell(row, cols["status"], new_status)
        if update.get("priority") is not None:
            priority = sanitize_cell(update["priority"]).upper()
            if priority not in PRIORITY_RANK:
                raise UpdateError(f"Unsupported priority for {requirement_id}: {priority}")
            if priority != cell(before, cols["priority"]):
                semantic_change = True
            set_cell(row, cols["priority"], priority)
        if update.get("dependencies") is not None:
            value = sanitize_cell(update["dependencies"]) or "—"
            if value != cell(before, cols["dependencies"]):
                semantic_change = True
            set_cell(row, cols["dependencies"], value)
        if update.get("owner") is not None:
            set_cell(row, cols["owner"], update["owner"])
        elif cell(row, cols["owner"]) in {"", "—", "-"} and new_status in {"In Progress", "Reported Complete", "Verified"}:
            set_cell(row, cols["owner"], args.actor)
        basis = sanitize_cell(update.get("status_basis", ""))
        if not basis and new_status != old_status:
            basis = {
                "Reported Complete": f"Owner report by {args.actor}", "Verified": f"Acceptance checked by {args.actor}",
                "In Progress": f"Owner update by {args.actor}", "Blocked": f"Blocker reported by {args.actor}",
                "Not Started": f"Baseline update by {args.actor}",
            }[new_status]
        if basis:
            if cols["basis"] is not None:
                set_cell(row, cols["basis"], basis)
            else:
                set_cell(row, cols["notes"], append_note(cell(row, cols["notes"]), f"状态依据：{basis}"))
        if update.get("completion_date") is not None:
            set_cell(row, cols["date"], validate_iso_date(str(update["completion_date"])))
        elif new_status in {"Reported Complete", "Verified"}:
            set_cell(row, cols["date"], change_date)
        elif new_status in {"Not Started", "In Progress", "Blocked"} and update.get("status") is not None:
            set_cell(row, cols["date"], "—")
        note = sanitize_cell(update.get("notes", ""))
        if evidence:
            evidence_items.append(f"{requirement_id}: {evidence}")
            note = append_note(note, f"Evidence: {evidence}")
        if note:
            set_cell(row, cols["notes"], append_note(cell(row, cols["notes"]), note))
        if row != before:
            transitions.append({"id": requirement_id, "old": old_status, "new": new_status})

    dep_cols = dcols(dependency_table.headers)
    dep_rows_by_id = {cell(row, dep_cols["id"]): row for row in dependency_table.rows}
    for update in dependency_updates:
        if not isinstance(update, dict) or not update.get("id"):
            raise UpdateError("Each dependency update must be an object with an 'id'")
        dependency_id = sanitize_cell(update["id"])
        if not DEPENDENCY_ID_RE.fullmatch(dependency_id):
            raise UpdateError(f"Dependency updates require one individual Q/R/C ID: {dependency_id}")
        if dependency_id in requested:
            raise UpdateError(f"Duplicate update ID: {dependency_id}")
        requested.add(dependency_id)
        row = dep_rows_by_id.get(dependency_id)
        if row is None:
            raise UpdateError(f"Unknown dependency ID: {dependency_id}")
        before = list(row)
        old_status = cell(row, dep_cols["status"])
        new_status = normalize_dependency_status(str(update.get("status", old_status)))
        evidence = flatten_evidence(update.get("evidence"))
        if new_status == "Resolved" and not evidence:
            raise UpdateError(f"{dependency_id} cannot become Resolved without evidence")
        set_cell(row, dep_cols["status"], new_status)
        if update.get("blocking_level") is not None:
            level = sanitize_cell(update["blocking_level"]).title()
            if level not in BLOCKING_LEVELS:
                raise UpdateError(f"Unsupported blocking level: {level}")
            if level != cell(before, dep_cols["level"], "Hard"):
                semantic_change = True
            set_cell(row, dep_cols["level"], level)
        if update.get("affects") is not None:
            value = sanitize_cell(update["affects"])
            if value != cell(before, dep_cols["affects"]):
                semantic_change = True
            set_cell(row, dep_cols["affects"], value)
        if update.get("owner") is not None:
            set_cell(row, dep_cols["owner"], update["owner"])
        elif cell(row, dep_cols["owner"]) in {"", "—", "-"} and new_status in {"In Progress", "Resolved"}:
            set_cell(row, dep_cols["owner"], args.actor)
        if update.get("due_date") is not None:
            set_cell(row, dep_cols["date"], validate_iso_date(str(update["due_date"])))
        note = sanitize_cell(update.get("notes", ""))
        if evidence:
            evidence_items.append(f"{dependency_id}: {evidence}")
            note = append_note(note, f"Evidence: {evidence}")
        if new_status == "Resolved" and old_status != "Resolved":
            note = append_note(note, f"Resolved on {change_date}")
        if note:
            set_cell(row, dep_cols["notes"], append_note(cell(row, dep_cols["notes"]), note))
        if row != before:
            transitions.append({"id": dependency_id, "old": old_status, "new": new_status})

    if not transitions:
        raise UpdateError("No effective changes; refusing to create a fake version bump")

    all_tables = progress_tables + [dependency_table]
    for table in sorted(all_tables, key=lambda item: item.header_index, reverse=True):
        lines[table.header_index : table.end_index] = render_table(table)

    old_version, new_version = update_version(lines, args.bump, args.new_version, "minor" if semantic_change else "patch")
    refreshed_dependencies = dependency_info(find_table(lines, DEPENDENCY_MARKER, DEPENDENCY_VARIANTS))
    recommendations = build_recommendations(ordered_rows, rows_by_id, refreshed_dependencies, args.recommend_limit)
    prefer_english = progress_tables[0].headers == PROGRESS_HEADERS_EN
    replace_next_steps(lines, recommendations, prefer_english)
    insert_changelog(lines, new_version, change_date, args.actor, transitions, "; ".join(evidence_items))

    content = "\n".join(lines) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output_path.parent, delete=False) as handle:
        handle.write(content)
        temporary_path = Path(handle.name)
    os.replace(temporary_path, output_path)
    print(json.dumps({
        "input": str(input_path), "input_sha256": actual_sha, "output": str(output_path),
        "old_version": old_version, "new_version": new_version, "transitions": transitions,
        "recommendation_targets": [item["target"] for item in recommendations], "unapplied": unapplied,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (UpdateError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SystemExit(f"error: {exc}")
