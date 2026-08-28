#!/usr/bin/env python3
"""Deterministically update canonical Living PRD progress tables and changelog."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


FUNCTIONAL_MARKER = "<!-- PRD-LIFECYCLE:FUNCTIONAL-PROGRESS -->"
TECHNICAL_MARKER = "<!-- PRD-LIFECYCLE:TECHNICAL-PROGRESS -->"
DEPENDENCY_MARKER = "<!-- PRD-LIFECYCLE:DEPENDENCY-REGISTER -->"
NEXT_START = "<!-- PRD-LIFECYCLE:NEXT-STEPS:START -->"
NEXT_END = "<!-- PRD-LIFECYCLE:NEXT-STEPS:END -->"
CHANGELOG_MARKER = "<!-- PRD-LIFECYCLE:CHANGELOG -->"

PROGRESS_HEADERS = ["ID", "需求项", "优先级", "状态", "负责人", "完成日期", "依赖", "备注/证据"]
DEPENDENCY_HEADERS = ["ID", "类型", "事项", "状态", "负责人", "截止日期", "备注/证据"]
CHANGELOG_HEADERS = ["版本", "日期", "更新人", "变更内容", "证据"]
ALLOWED_STATUSES = {"Not Started", "In Progress", "Blocked", "Reported Complete", "Verified"}
STATUS_ALIASES = {
    "未开始": "Not Started",
    "进行中": "In Progress",
    "阻塞": "Blocked",
    "已完成": "Reported Complete",
    "已报告完成": "Reported Complete",
    "已验证": "Verified",
}
DEPENDENCY_STATUSES = {"Open", "In Progress", "Resolved"}
DEPENDENCY_STATUS_ALIASES = {"未解决": "Open", "进行中": "In Progress", "已解决": "Resolved", "关闭": "Resolved"}
PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2}
STATUS_RANK = {"Reported Complete": 0, "In Progress": 1, "Not Started": 2}
DEPENDENCY_ID_RE = re.compile(r"\b(?:FR|TR|NFR|Q|R)(?:-[A-Z0-9]+)*-\d{3}\b")
VERSION_RE = re.compile(r"^(\|\s*PRD 文档版本\s*\|\s*)v(\d+)\.(\d+)\.(\d+)(\s*\|.*)$")


class UpdateError(ValueError):
    pass


def parse_md_row(line: str) -> list[str]:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        raise UpdateError(f"Invalid Markdown table row: {line}")
    return [cell.replace("\\|", "|").strip() for cell in re.split(r"(?<!\\)\|", stripped[1:-1])]


def render_md_row(cells: list[str]) -> str:
    safe = [str(cell).replace("|", "\\|").strip() or "—" for cell in cells]
    return "| " + " | ".join(safe) + " |"


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def find_table(lines: list[str], marker: str, expected_headers: list[str]) -> tuple[int, int, list[str], list[list[str]]]:
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
    if headers != expected_headers:
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
    return header_index, row_index, headers, rows


def normalize_status(value: str) -> str:
    status = STATUS_ALIASES.get(value.strip(), value.strip())
    if status not in ALLOWED_STATUSES:
        raise UpdateError(f"Unsupported delivery status: {value}")
    return status


def validate_iso_date(value: str) -> str:
    try:
        return dt.date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise UpdateError(f"Invalid ISO date: {value}") from exc


def append_note(existing: str, addition: str) -> str:
    addition = addition.strip()
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
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def normalize_title(value: str) -> str:
    return re.sub(r"[\s\-—_：:（）()]+", "", value).casefold()


def resolve_progress_row(update: dict[str, Any], rows_by_id: dict[str, list[str]], rows: list[list[str]]) -> tuple[str, list[str]]:
    raw_id = update.get("id")
    if raw_id:
        requirement_id = str(raw_id).strip()
        row = rows_by_id.get(requirement_id)
        if row is None:
            raise UpdateError(f"Unknown requirement ID: {requirement_id}")
        return requirement_id, row

    raw_title = update.get("title")
    if not raw_title:
        raise UpdateError("Each progress update must contain an 'id' or unique 'title'")
    target = normalize_title(str(raw_title))
    exact = [row for row in rows if normalize_title(row[1]) == target]
    if len(exact) == 1:
        return exact[0][0], exact[0]
    partial = [row for row in rows if target in normalize_title(row[1]) or normalize_title(row[1]) in target]
    if len(partial) == 1:
        return partial[0][0], partial[0]
    candidates = ", ".join(row[0] for row in (exact or partial)) or "none"
    raise UpdateError(f"Ambiguous or unmatched requirement title '{raw_title}'; candidates: {candidates}")


def normalize_dependency_status(value: str) -> str:
    status = DEPENDENCY_STATUS_ALIASES.get(value.strip(), value.strip())
    if status not in DEPENDENCY_STATUSES:
        raise UpdateError(f"Unsupported dependency status: {value}")
    return status


def bump_version(version: tuple[int, int, int], bump: str) -> tuple[int, int, int]:
    major, minor, patch = version
    if bump == "major":
        return major + 1, 0, 0
    if bump == "minor":
        return major, minor + 1, 0
    return major, minor, patch + 1


def update_version(lines: list[str], bump: str, explicit: str | None) -> tuple[str, str]:
    for index, line in enumerate(lines):
        match = VERSION_RE.match(line)
        if not match:
            continue
        old_tuple = tuple(int(match.group(i)) for i in (2, 3, 4))
        if explicit:
            explicit_match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", explicit.strip())
            if not explicit_match:
                raise UpdateError(f"Invalid explicit version: {explicit}")
            new_tuple = tuple(int(explicit_match.group(i)) for i in (1, 2, 3))
        else:
            new_tuple = bump_version(old_tuple, bump)
        old_version = "v" + ".".join(map(str, old_tuple))
        new_version = "v" + ".".join(map(str, new_tuple))
        lines[index] = f"{match.group(1)}{new_version}{match.group(5)}"
        return old_version, new_version
    raise UpdateError("Could not find '| PRD 文档版本 | vX.Y.Z |' metadata row")


def dependency_is_unresolved(
    dep: str, rows_by_id: dict[str, list[str]], dependencies_by_id: dict[str, list[str]]
) -> bool:
    normalized = dep.strip()
    if normalized in {"", "—", "-", "无", "None", "none"}:
        return False
    ids = DEPENDENCY_ID_RE.findall(normalized)
    if not ids:
        return True
    for dependency_id in ids:
        dependency = rows_by_id.get(dependency_id)
        if dependency is not None and dependency[3] == "Verified":
            continue
        registered = dependencies_by_id.get(dependency_id)
        if registered is not None and registered[3] == "Resolved":
            continue
        if dependency is None and registered is None:
            return True
        if dependency is not None or registered is not None:
            return True
    return False


def build_recommendations(
    rows: list[list[str]],
    rows_by_id: dict[str, list[str]],
    dependencies_by_id: dict[str, list[str]],
    limit: int,
) -> list[tuple[str, str, str, str, str, str]]:
    candidates: list[tuple[int, int, int, int, list[str]]] = []
    dependency_candidates: dict[str, tuple[int, int, int, int, tuple[str, str, str, str, str, str]]] = {}
    for order, row in enumerate(rows):
        requirement_id, title, priority, status, _owner, _date, dependencies, _notes = row
        unresolved = dependency_is_unresolved(dependencies, rows_by_id, dependencies_by_id)
        if status == "Blocked" or unresolved:
            dependency_ids = DEPENDENCY_ID_RE.findall(dependencies)
            if dependency_ids:
                for dependency_id in dependency_ids:
                    requirement_dependency = rows_by_id.get(dependency_id)
                    if requirement_dependency is not None:
                        # That requirement will be recommended normally when it is itself actionable.
                        continue
                    registered = dependencies_by_id.get(dependency_id)
                    if registered is not None and registered[3] != "Resolved":
                        _id, _type, item, _state, dep_owner, due_date, dep_notes = registered
                        recommendation = (
                            dependency_id,
                            f"解决“{item}”",
                            f"该依赖正在阻塞 {requirement_id}（{priority}）",
                            dep_owner if dep_owner not in {"", "—", "-"} else "依赖负责人",
                            due_date if due_date not in {"", "—", "-"} else "下次评审前",
                            dep_notes if dep_notes not in {"", "—", "-"} else "决策或风险关闭记录",
                        )
                        dependency_candidates[dependency_id] = (
                            PRIORITY_RANK.get(priority, 99),
                            -1,
                            -1,
                            order,
                            recommendation,
                        )
                    elif registered is None:
                        recommendation = (
                            dependency_id,
                            f"确认并解除依赖 {dependency_id}",
                            f"该依赖正在阻塞 {requirement_id}（{priority}）",
                            "依赖负责人",
                            "下次评审前",
                            "依赖解除或书面决策记录",
                        )
                        dependency_candidates[dependency_id] = (
                            PRIORITY_RANK.get(priority, 99),
                            -1,
                            -1,
                            order,
                            recommendation,
                        )
            elif dependencies not in {"", "—", "-", "无", "None", "none"}:
                key = f"{requirement_id}:dependency"
                recommendation = (
                    requirement_id,
                    f"先解除依赖“{dependencies}”",
                    f"该外部依赖正在阻塞 {requirement_id}（{priority}）",
                    "依赖负责人",
                    "下次评审前",
                    "依赖解除确认",
                )
                dependency_candidates[key] = (
                    PRIORITY_RANK.get(priority, 99), -1, -1, order, recommendation
                )
            elif status == "Blocked":
                key = f"{requirement_id}:blocker"
                recommendation = (
                    requirement_id,
                    f"明确“{title}”的阻塞原因",
                    f"{requirement_id} 标记为 Blocked，但没有记录依赖",
                    _owner if _owner not in {"", "—", "-"} else "需求负责人",
                    "下次评审前",
                    "已编号的依赖或解除阻塞记录",
                )
                dependency_candidates[key] = (
                    PRIORITY_RANK.get(priority, 99), -1, -1, order, recommendation
                )
            continue
        if status not in STATUS_RANK:
            continue
        downstream_count = sum(
            1
            for other in rows
            if other[3] != "Verified" and requirement_id in DEPENDENCY_ID_RE.findall(other[6])
        )
        candidates.append((PRIORITY_RANK.get(priority, 99), STATUS_RANK[status], -downstream_count, order, row))
    candidates.sort(key=lambda item: item[:4])

    recommendations: list[tuple[str, str, str, str, str, str]] = []
    merged: list[tuple[int, int, int, int, Any]] = list(dependency_candidates.values()) + candidates
    merged.sort(key=lambda item: item[:4])
    for _priority_rank, _status_rank, _negative_downstream, _order, item in merged[:limit]:
        if isinstance(item, tuple):
            recommendations.append(item)
            continue
        row = item
        requirement_id, title, priority, status, owner, _date, _dependencies, notes = row
        if status == "Reported Complete":
            action = f"验证“{title}”"
            reason = f"{priority}，已报告完成且依赖已解除；补充约定证据后可转为 Verified"
        elif status == "In Progress":
            action = f"继续“{title}”"
            reason = f"{priority}，正在进行且没有未解决依赖"
        else:
            action = f"开始“{title}”"
            reason = f"{priority}，尚未开始且没有未解决依赖"
        if owner not in {"", "—", "-"}:
            reason += f"；负责人：{owner}"
        if notes not in {"", "—", "-"}:
            reason += f"；证据/备注：{notes}"
        suggested_owner = owner if owner not in {"", "—", "-"} else "需求负责人"
        if status == "Reported Complete":
            expected_evidence = "与验收标准对应的测试或评审记录"
        elif status == "In Progress":
            expected_evidence = "下一个明确检查点的交付物"
        else:
            expected_evidence = "首个可验证交付物"
        recommendations.append((requirement_id, action, reason, suggested_owner, "待负责人排期", expected_evidence))
    return recommendations


def replace_next_steps(lines: list[str], recommendations: list[tuple[str, str, str, str, str, str]]) -> None:
    try:
        start = lines.index(NEXT_START)
        end = lines.index(NEXT_END, start + 1)
    except ValueError as exc:
        raise UpdateError("Missing next-step marker block") from exc

    block = [
        NEXT_START,
        "| ID | 推荐动作 | 原因 | 建议负责人 | 目标日期 | 完成证据 |",
        "|---|---|---|---|---|---|",
    ]
    if recommendations:
        block.extend(render_md_row(list(item)) for item in recommendations)
    else:
        block.append("| — | 当前没有可直接推荐的未完成项 | 所有事项均已 Verified | — | — | — |")
    block.append(NEXT_END)
    lines[start : end + 1] = block


def insert_changelog(
    lines: list[str], version: str, date: str, actor: str, changes: list[dict[str, str]], evidence: str
) -> None:
    header_index, _end, _headers, _rows = find_table(lines, CHANGELOG_MARKER, CHANGELOG_HEADERS)
    summary = "; ".join(f"{item['id']}: {item['old_status']}→{item['new_status']}" for item in changes)
    row = render_md_row([version, date, actor, summary, evidence or "—"])
    lines.insert(header_index + 2, row)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prd", required=True, help="Input canonical Markdown PRD")
    parser.add_argument("--updates", required=True, help="JSON file containing an updates array")
    parser.add_argument("--output", required=True, help="New Markdown PRD path; must differ from input")
    parser.add_argument("--actor", required=True, help="Person or stable employee identifier")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="ISO completion/change date")
    parser.add_argument("--bump", choices=("patch", "minor", "major"), default="patch")
    parser.add_argument("--new-version", help="Explicit vX.Y.Z override")
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

    payload = json.loads(Path(args.updates).read_text(encoding="utf-8"))
    updates = payload.get("updates", [])
    dependency_updates = payload.get("dependency_updates", [])
    unapplied = payload.get("unapplied", [])
    if not isinstance(updates, list) or not isinstance(dependency_updates, list):
        raise UpdateError("'updates' and 'dependency_updates' must be arrays")
    if not updates and not dependency_updates:
        raise UpdateError("Updates JSON must contain a non-empty update array")
    if not isinstance(unapplied, list):
        raise UpdateError("'unapplied' must be an array when provided")

    lines = input_path.read_text(encoding="utf-8").splitlines()
    tables: list[tuple[int, int, list[str], list[list[str]]]] = [
        find_table(lines, FUNCTIONAL_MARKER, PROGRESS_HEADERS),
        find_table(lines, TECHNICAL_MARKER, PROGRESS_HEADERS),
    ]
    dependency_table = find_table(lines, DEPENDENCY_MARKER, DEPENDENCY_HEADERS)
    rows_by_id: dict[str, list[str]] = {}
    ordered_rows: list[list[str]] = []
    for _start, _end, _headers, rows in tables:
        for row in rows:
            requirement_id = row[0]
            if requirement_id in rows_by_id:
                raise UpdateError(f"Duplicate requirement ID: {requirement_id}")
            rows_by_id[requirement_id] = row
            ordered_rows.append(row)

    dependencies_by_id: dict[str, list[str]] = {}
    dependency_rows = dependency_table[3]
    for row in dependency_rows:
        dependency_id = row[0]
        if dependency_id in dependencies_by_id or dependency_id in rows_by_id:
            raise UpdateError(f"Duplicate tracked ID: {dependency_id}")
        dependencies_by_id[dependency_id] = row

    requested_ids: set[str] = set()
    transitions: list[dict[str, str]] = []
    evidence_items: list[str] = []
    for update in updates:
        if not isinstance(update, dict):
            raise UpdateError("Each progress update must be an object")
        requirement_id, row = resolve_progress_row(update, rows_by_id, ordered_rows)
        if requirement_id in requested_ids:
            raise UpdateError(f"Duplicate update ID: {requirement_id}")
        requested_ids.add(requirement_id)

        old_status = row[3]
        new_status = normalize_status(str(update.get("status", old_status)))
        evidence = flatten_evidence(update.get("evidence"))
        if new_status == "Verified" and (
            update.get("verification_confirmed") is not True or not evidence
        ):
            raise UpdateError(
                f"{requirement_id} cannot become Verified without evidence and verification_confirmed=true"
            )
        row[3] = new_status
        if update.get("priority") is not None:
            priority = str(update["priority"]).strip().upper()
            if priority not in PRIORITY_RANK:
                raise UpdateError(f"Unsupported priority for {requirement_id}: {priority}")
            row[2] = priority
        if update.get("owner") is not None:
            row[4] = str(update["owner"]).strip() or "—"
        elif row[4] in {"", "—", "-"} and new_status in {"In Progress", "Reported Complete", "Verified"}:
            row[4] = args.actor

        if update.get("completion_date") is not None:
            row[5] = validate_iso_date(str(update["completion_date"]))
        elif new_status in {"Reported Complete", "Verified"}:
            row[5] = change_date
        elif new_status in {"Not Started", "In Progress", "Blocked"} and update.get("status") is not None:
            row[5] = "—"

        if update.get("dependencies") is not None:
            row[6] = str(update["dependencies"]).strip() or "—"
        note = str(update.get("notes", "")).strip()
        if evidence:
            evidence_items.append(f"{requirement_id}: {evidence}")
            note = append_note(note, f"证据：{evidence}")
        row[7] = append_note(row[7], note)
        transitions.append({"id": requirement_id, "old_status": old_status, "new_status": new_status})

    for update in dependency_updates:
        if not isinstance(update, dict) or not update.get("id"):
            raise UpdateError("Each dependency update must be an object with an 'id'")
        dependency_id = str(update["id"]).strip()
        if dependency_id in requested_ids:
            raise UpdateError(f"Duplicate update ID: {dependency_id}")
        requested_ids.add(dependency_id)
        row = dependencies_by_id.get(dependency_id)
        if row is None:
            raise UpdateError(f"Unknown dependency ID: {dependency_id}")
        old_status = row[3]
        new_status = normalize_dependency_status(str(update.get("status", old_status)))
        evidence = flatten_evidence(update.get("evidence"))
        if new_status == "Resolved" and not evidence:
            raise UpdateError(f"{dependency_id} cannot become Resolved without evidence")
        row[3] = new_status
        if update.get("owner") is not None:
            row[4] = str(update["owner"]).strip() or "—"
        elif row[4] in {"", "—", "-"} and new_status in {"In Progress", "Resolved"}:
            row[4] = args.actor
        if update.get("due_date") is not None:
            row[5] = validate_iso_date(str(update["due_date"]))
        note = str(update.get("notes", "")).strip()
        if evidence:
            evidence_items.append(f"{dependency_id}: {evidence}")
            note = append_note(note, f"证据：{evidence}")
        if new_status == "Resolved":
            note = append_note(note, f"解决日期：{change_date}")
        row[6] = append_note(row[6], note)
        transitions.append({"id": dependency_id, "old_status": old_status, "new_status": new_status})

    # Re-render progress tables. Row counts do not change, so stored ranges remain valid.
    all_tables = tables + [dependency_table]
    for start, end, headers, rows in sorted(all_tables, key=lambda item: item[0], reverse=True):
        replacement = [render_md_row(headers), "|" + "---|" * len(headers)]
        replacement.extend(render_md_row(row) for row in rows)
        lines[start:end] = replacement

    old_version, new_version = update_version(lines, args.bump, args.new_version)
    recommendations = build_recommendations(
        ordered_rows, rows_by_id, dependencies_by_id, max(args.recommend_limit, 0)
    )
    replace_next_steps(lines, recommendations)
    insert_changelog(lines, new_version, change_date, args.actor, transitions, "; ".join(evidence_items))

    content = "\n".join(lines) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output_path.parent, delete=False) as handle:
        handle.write(content)
        temporary_path = Path(handle.name)
    os.replace(temporary_path, output_path)

    print(
        json.dumps(
            {
                "input": str(input_path),
                "output": str(output_path),
                "old_version": old_version,
                "new_version": new_version,
                "transitions": transitions,
                "recommendations": [item[0] for item in recommendations],
                "unapplied": unapplied,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (UpdateError, json.JSONDecodeError) as exc:
        raise SystemExit(f"error: {exc}")
