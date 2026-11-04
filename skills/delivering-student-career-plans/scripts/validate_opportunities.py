"""Check linked job/company/compensation evidence in the live plan text."""

import re
from urllib.parse import urlparse


def validate_opportunities(payload, route_keys, text):
    checks = payload.get("opportunity_checks")
    rows = checks.get("rows") if isinstance(checks, dict) else None
    if not isinstance(rows, list) or not rows:
        return ["career_plan opportunities: missing linked company-role-compensation rows"]

    required = (
        "company", "role", "city", "recruitment_type", "fit", "salary_text",
        "benefits_text", "source_url", "access_date",
    )
    covered, salaried, errors = set(), set(), []
    routes = {key for key in route_keys if isinstance(key, str) and key.strip()} if isinstance(route_keys, list) else set()
    if not routes:
        errors.append("career_plan opportunities: missing route keys")
    for index, row in enumerate(rows, 1):
        label = f"career_plan opportunities: row {index}"
        if not isinstance(row, dict):
            errors.append(f"{label} is not an object")
            continue
        row_errors = []
        route = row.get("route_key")
        if not isinstance(route, str) or route not in routes:
            row_errors.append(f"{label} has an unknown route")
        excerpt = row.get("evidence_excerpt")
        if not isinstance(excerpt, str) or not excerpt.strip() or excerpt not in text:
            row_errors.append(f"{label} excerpt is absent from live text")
            excerpt = ""
        elif len(excerpt) > 1800:
            row_errors.append(f"{label} excerpt must describe one opportunity, not the whole plan")
        for field in required:
            value = row.get(field)
            if not isinstance(value, str) or not value.strip():
                row_errors.append(f"{label} missing {field}")
            elif field == "access_date":
                if value not in text:
                    row_errors.append(f"{label} access date is absent from live text")
            elif field == "source_url":
                marker = row.get("source_marker")
                footnote = (
                    isinstance(marker, str) and bool(marker.strip()) and marker in excerpt
                    and any(marker in line and value in line for line in text.splitlines())
                )
                if value not in excerpt and not footnote:
                    row_errors.append(f"{label} source URL is not linked to this opportunity")
            elif value not in excerpt:
                row_errors.append(f"{label} {field} is not linked in the same live excerpt")
        url = urlparse(str(row.get("source_url", "")))
        if url.scheme not in {"http", "https"} or not url.netloc:
            row_errors.append(f"{label} source URL is invalid")
        if not re.fullmatch(r"20\d{2}(?:-\d{2}-\d{2}|年\d{1,2}月\d{1,2}日)", str(row.get("access_date", ""))):
            row_errors.append(f"{label} access date is invalid")
        if row.get("sample_status") not in {"current_sample", "historical_sample", "research_only"}:
            row_errors.append(f"{label} sample status is missing")

        salary_type = row.get("salary_type")
        salary = str(row.get("salary_text", ""))
        if salary_type not in {"company_disclosed", "comparable_sample", "undisclosed"}:
            row_errors.append(f"{label} salary type is invalid")
        elif salary_type == "undisclosed":
            if not re.search(r"未披露|未公开|未公示|待确认|不详", salary):
                row_errors.append(f"{label} undisclosed salary is not identified")
        else:
            if re.search(r"目标|期望|预期|希望|想要", salary):
                row_errors.append(f"{label} personal salary target is not market evidence")
            if not re.search(r"\d", salary) or not re.search(r"元|万|[kKwW]|HKD|USD|EUR|RMB|CNY|GBP|[¥￥$€£]", salary):
                row_errors.append(f"{label} salary needs a number and unit")
            if salary_type == "comparable_sample":
                note = row.get("comparability_note")
                if row.get("salary_route_key") != route:
                    row_errors.append(f"{label} comparable salary belongs to another route")
                if not isinstance(note, str) or not note.strip() or note not in excerpt:
                    row_errors.append(f"{label} comparable salary basis is absent from live text")
        if not row_errors:
            covered.add(route)
            if salary_type != "undisclosed" and row.get("sample_status") != "research_only":
                salaried.add(route)
        errors.extend(row_errors)

    for route in sorted(routes - covered):
        errors.append(f"career_plan opportunities: route {route} has no complete company-role-benefits evidence")
    for route in sorted(routes - salaried):
        errors.append(f"career_plan opportunities: route {route} salary research remains incomplete")
    return errors
