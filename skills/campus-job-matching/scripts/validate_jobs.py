#!/usr/bin/env python3
"""Offline evidence gate. Does not crawl, log in, submit applications or write Feishu.

Only ready-output is eligible for an authorized append. A pass proves the supplied
evidence contract is complete and consistent; it does not authenticate page facts.
"""
from __future__ import annotations

import argparse
import calendar
from collections import Counter
from datetime import date, datetime, time, timedelta
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")
COMMON_CHECKS = ("subject", "role", "degree", "major", "city", "employment")
MODE_CHECKS = {"campus": ("graduation",), "internship": ("student_status", "schedule"),
               "experienced": ("experience", "seniority", "salary")}
CLOSED = re.compile(
    r"(?:该|本|此)?(?:职位|岗位)(?:已|已经)?(?:停止招聘|停止投递|停止接受(?:申请|简历)|下线|下架|关闭|不存在|招满|过期|结束)"
    r"|(?:已|已经)(?:停止招聘|停止投递|停止接受(?:申请|简历))"
    r"|(?:招聘|网申|投递)(?:已|已经)结束|no longer (?:accepting applications|available)"
    r"|this (?:job|position|role|posting) (?:has been|is) (?:closed|filled|expired)", re.I)
BLOCKED_HTTP = {401, 403, 405, 429}


def web_url(value):
    try:
        part = urlsplit(str(value or ""))
        return part.scheme.lower() in {"http", "https"} and bool(part.hostname)
    except ValueError:
        return False


def canonical_url(value):
    # Keep SPA fragments, job IDs and semantic query parameters.
    value = str(value or "").strip()
    match = re.fullmatch(r"\[[^\]]*\]\((https?://[^\s]+)\)", value)
    value = match.group(1) if match else value
    if not web_url(value):
        return ""
    p = urlsplit(value)
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith("utm_")]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"),
                       urlencode(sorted(query)), p.fragment))


def job_key(row):
    tenant, job_id = str(row.get("tenant") or "").strip().casefold(), str(row.get("job_id") or "").strip()
    if tenant and job_id:
        return "id:" + tenant + ":" + job_id
    return canonical_url(row.get("url"))


def company_key(row):
    # company_key is an explicitly verified alias, not an inferred parent group.
    return " ".join(str(row.get("company_key") or row.get("company") or "").split()).casefold()


def checked_time(value):
    result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("核验时间缺少时区")
    return result


def deadline_time(value):
    value = str(value or "").strip()
    if not value or value.startswith("0001-") or value in {"未公布", "截止未公布", "Open"}:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return datetime.combine(date.fromisoformat(value), time.max, TZ)
    return checked_time(value)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def has_text(value):
    return isinstance(value, str) and bool(value.strip())


def search_mode(profile):
    # Missing mode retains the previous campus contract; new runs set it explicitly.
    return profile.get("search_mode", "campus")


def mode_checks(profile):
    mode = search_mode(profile)
    return COMMON_CHECKS + MODE_CHECKS.get(mode, ()) if isinstance(mode, str) else COMMON_CHECKS


def nonnegative(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def mode_issues(profile, job):
    """Only compare explicitly normalized facts; never invent experience or salary."""
    rejected, pending = [], []
    mode = search_mode(profile)
    if mode == "experienced":
        req, exp = job.get("experience_requirement"), profile.get("experience")
        if not isinstance(req, dict) or not nonnegative(req.get("min_months")) or req.get("basis") not in ("formal_work", "relevant_work") or req.get("priority") not in ("mandatory", "preferred", "none", "unknown"):
            pending.append("社招工作经验要求未标准化")
        elif req["priority"] == "unknown" or (req["priority"] == "none" and req["min_months"] != 0):
            pending.append("社招工作经验门槛仍未知或矛盾")
        elif isinstance(exp, dict):
            months = exp.get("verified_work_months" if req["basis"] == "formal_work" else "relevant_work_months")
            if nonnegative(months) and req["priority"] == "mandatory" and months < req["min_months"]:
                rejected.append("已核实的正式/相关工作月数低于社招必备门槛；不计实习")
    if mode == "internship":
        req, avail = job.get("internship_requirement"), profile.get("internship_availability")
        if not isinstance(req, dict) or not all(nonnegative(req.get(k)) for k in ("days_per_week", "months")) or req.get("days_per_week", 8) > 7 or not isinstance(req.get("student_only"), bool):
            pending.append("实习在校身份/出勤要求未标准化")
        else:
            if req["student_only"] and profile.get("student_status") == "graduated":
                rejected.append("仅限在校生实习与当前身份不符")
            if isinstance(avail, dict):
                if any(nonnegative(avail.get(k)) and avail[k] < req[k] for k in ("days_per_week", "months")):
                    rejected.append("实习可出勤天数或持续月数不足")
                if req.get("latest_start_date"):
                    try:
                        if date.fromisoformat(avail.get("start_date")) > date.fromisoformat(req["latest_start_date"]):
                            rejected.append("实习可到岗日期晚于岗位要求")
                    except (ValueError, TypeError):
                        pending.append("实习到岗日期无法解析")
    constraint = profile.get("salary_constraint")
    if constraint is not None:
        if not isinstance(constraint, dict) or not nonnegative(constraint.get("min")) or not has_text(constraint.get("currency")) or constraint.get("period") not in ("month", "year") or not isinstance(constraint.get("hard"), bool):
            pending.append("薪资偏好/硬底线格式不明")
        elif constraint["hard"]:
            salary = job.get("salary_range")
            if not isinstance(salary, dict) or not all(nonnegative(salary.get(k)) for k in ("min", "max")) or salary["min"] > salary["max"]:
                pending.append("设置薪资硬底线但岗位薪资范围未知/无效")
            elif any(salary.get(k) != constraint[k] for k in ("currency", "period")):
                pending.append("薪资币种/周期不一致，不能直接比较")
            elif salary["max"] < constraint["min"]:
                rejected.append("岗位公布薪资上限低于本人硬底线")
    return rejected, pending


def date_span(value):
    value = str(value)
    if re.fullmatch(r"\d{4}-\d{2}", value):
        year, month = map(int, value.split("-"))
        return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
    result = date.fromisoformat(value)
    return result, result


def resume_sources(profile):
    """Bind the reviewed original and its complete extraction; never infer latestness."""
    errors, hashes, resume_text = [], {}, ""
    for field, name in (("resume_file", "resume_file"), ("resume_text_file", "resume_text")):
        try:
            path = Path(str(profile.get(field) or ""))
            if not path.is_absolute() or not path.is_file():
                raise ValueError("缺少本地绝对路径")
            content = path.read_bytes()
            if not content:
                raise ValueError("文件为空")
            hashes[name] = hashlib.sha256(content).hexdigest()
            if name == "resume_text":
                resume_text = content.decode("utf-8-sig")
                if not resume_text.strip():
                    raise ValueError("提取正文为空")
        except (OSError, ValueError, UnicodeError) as exc:
            errors.append("简历来源不可核验：" + field + "（" + str(exc) + "）")
    return errors, hashes, resume_text


def review_issues(profile, job, now, max_age_hours, sources):
    """Check a fresh semantic review's evidence contract, not the truth of its judgment."""
    rejected, pending = [], []
    review = job.get("final_review")
    if not isinstance(review, dict):
        return [], ["缺少最新简历×完整JD独立终审"]
    if review.get("method") != "fresh_resume_jd" or not has_text(review.get("summary")):
        pending.append("终审缺少独立复核方法或具体结论")
    if review.get("verdict") == "reject":
        rejected.append("独立人岗终审不推荐")
    elif review.get("verdict") != "recommend":
        pending.append("独立人岗终审尚未明确推荐")
    if review.get("job_key") != job_key(job):
        pending.append("终审不对应当前岗位唯一键")
    try:
        age = now - checked_time(review.get("reviewed_at"))
        if age > timedelta(hours=max_age_hours) or age < -timedelta(minutes=5):
            pending.append("独立终审过期或时间异常")
    except (ValueError, TypeError):
        pending.append("缺少带时区的实际终审时间")
    source_errors, hashes, resume_text = sources
    pending.extend(source_errors)
    expected = dict(hashes, jd_text=hashlib.sha256(str(job.get("jd_text") or "").encode()).hexdigest(),
                    profile=fingerprint(profile))
    bound = review.get("source_hashes")
    if not isinstance(bound, dict) or any(bound.get(k) != v for k, v in expected.items()):
        pending.append("终审来源指纹与当前简历/提取正文/JD/画像不一致，需重审")
    conditions = review.get("hard_conditions")
    for key in (k for k in mode_checks(profile) if k not in ("subject", "role")):
        item = conditions.get(key) if isinstance(conditions, dict) else None
        if isinstance(item, dict) and item.get("status") == "fail":
            rejected.append("终审硬条件不符：" + key)
        elif not isinstance(item, dict) or item.get("status") != "pass" or not has_text(item.get("reason")):
            pending.append("终审硬条件缺少独立判断：" + key)
    normalize = lambda value: re.sub(r"\s+", "", str(value or ""))
    jd, resume = normalize(job.get("jd_text")), normalize(resume_text)
    supported_duties = 0
    for group in ("duties", "requirements"):
        items = review.get(group)
        if not isinstance(items, list) or not items:
            pending.append("终审未逐项覆盖：" + group)
            continue
        for item in items:
            if not isinstance(item, dict):
                pending.append("终审证据条目格式错误：" + group)
                continue
            jq, rq = normalize(item.get("jd_quote")), normalize(item.get("resume_quote"))
            if not has_text(item.get("jd_quote")) or jq not in jd or not has_text(item.get("reason")):
                pending.append("终审JD引文不存在于当前完整JD或缺判断理由")
            if not isinstance(item.get("resume_quote"), str):
                pending.append("终审简历引文必须为字符串；无证据使用空串")
            positive = item.get("assessment") in (("direct", "transferable") if group == "duties" else ("met",))
            if positive and (not has_text(item.get("resume_quote")) or rq not in resume):
                pending.append("终审匹配引文不存在于本次简历正文")
            if group == "duties":
                if item.get("assessment") not in ("direct", "transferable", "gap", "unknown"):
                    pending.append("终审职责判定未明确")
                if positive and jq and jq in jd and rq and rq in resume:
                    supported_duties += 1
            else:
                if item.get("priority") not in ("mandatory", "preferred") or item.get("assessment") not in ("met", "gap", "unknown"):
                    pending.append("终审要求未区分必须/优先或匹配状态")
                if item.get("priority") == "mandatory":
                    if item.get("assessment") == "gap":
                        rejected.append("终审发现必备能力缺口：" + str(item.get("jd_quote") or ""))
                    elif item.get("assessment") != "met":
                        pending.append("终审必备要求仍未知")
    if not supported_duties:
        pending.append("终审无核心职责与简历的直接/可迁移证据配对")
    if not isinstance(review.get("gaps"), list) or any(not has_text(x) for x in review.get("gaps", [])):
        pending.append("终审未明确记录差距（无差距使用空数组）")
    opens = review.get("open_items")
    if not isinstance(opens, list):
        pending.append("终审未记录Open项（无Open使用空数组）")
    else:
        for item in opens:
            if not isinstance(item, dict) or not has_text(item.get("item")) or not isinstance(item.get("blocking"), bool):
                pending.append("终审Open项缺少内容或是否阻断的判断")
            elif item["blocking"]:
                pending.append("终审仍有阻断Open：" + item["item"])
    return rejected, pending


def profile_errors(profile):
    errors = []
    mode = search_mode(profile)
    if not isinstance(mode, str) or mode not in MODE_CHECKS:
        errors.append("选岗模式必须为campus/internship/experienced")
    for key in (("student_id", "degree", "major") if mode in ("campus", "internship") else ("student_id",)):
        if not str(profile.get(key) or "").strip() or profile.get(key) == "Open":
            errors.append("学生必需条件未确定：" + key)
    if mode == "campus":
        try:
            if not re.fullmatch(r"\d{4}-\d{2}(?:-\d{2})?", str(profile.get("graduation_date") or "")):
                raise ValueError()
            date_span(profile.get("graduation_date"))
        except (ValueError, TypeError):
            errors.append("毕业年月未确定，不能自行归届")
    if mode == "experienced":
        exp = profile.get("experience")
        if not isinstance(exp, dict) or not all(nonnegative(exp.get(k)) for k in ("verified_work_months", "relevant_work_months")):
            errors.append("缺少已核实的正式及相关工作月数；未知不填0")
        elif exp["relevant_work_months"] > exp["verified_work_months"]:
            errors.append("相关正式工作月数超过正式工作总月数")
    if mode == "internship":
        avail = profile.get("internship_availability")
        if profile.get("student_status") not in ("enrolled", "graduated"):
            errors.append("实习在校/毕业身份未确认")
        if not isinstance(avail, dict) or not all(nonnegative(avail.get(k)) and avail[k] > 0 for k in ("days_per_week", "months")) or avail.get("days_per_week", 8) > 7:
            errors.append("实习每周可出勤天数/持续月数未确认")
        try:
            date.fromisoformat(avail.get("start_date") if isinstance(avail, dict) else "")
        except (ValueError, TypeError):
            errors.append("实习可到岗日期未确认")
    for key in ("target_roles", "cities", "employment_types"):
        if not isinstance(profile.get(key), list) or not profile[key] or any(not str(x).strip() or x == "Open" for x in profile[key]):
            errors.append("学生必需条件未确定：" + key)
    return errors


def check_job(profile, job, now, max_age_hours=24, sources=None):
    rejected, blocked, pending = [], [], []
    if job.get("student_id") != profile.get("student_id"):
        rejected.append("学生身份与本轮画像不一致")
    for key in ("company", "title", "jd_text", "match_evidence", "gaps"):
        if not str(job.get(key) or "").strip():
            pending.append("缺少 " + key)
    if not canonical_url(job.get("url")) or not job_key(job):
        pending.append("缺少可追溯的岗位链接/唯一键")
    if job.get("link_type") not in {"detail", "official_list", "employer_platform", "recruiter_platform"}:
        pending.append("链接类型未明确或仅为线索")
    application = job.get("application") or {}
    if application.get("route", "form") not in ("form", "chat"):
        pending.append("申请路径必须明确为表单或沟通")
    if job.get("source_platform") == "boss" and application.get("route") != "chat":
        pending.append("BOSS岗位必须使用沟通入口核验，不能套用官网表单")
    if job.get("link_type") == "recruiter_platform" and not has_text(job.get("source_platform")):
        pending.append("招聘平台岗位缺少平台标识")
    cities = job.get("cities")
    if not isinstance(cities, list) or not cities:
        pending.append("实际工作城市未确认")
    elif profile.get("cities") and not set(cities).intersection(profile["cities"]):
        rejected.append("城市不在学生接受范围")
    employment = job.get("employment_type")
    if not employment:
        pending.append("全职/实习类型未确认")
    elif profile.get("employment_types") and employment not in profile["employment_types"]:
        rejected.append("全职/实习类型不符合学生要求")
    if search_mode(profile) in ("campus", "experienced") and employment == "internship":
        rejected.append("校招全职/社招模式不能混入实习；实习另起明确模式")
    if search_mode(profile) == "internship" and employment and employment != "internship":
        rejected.append("实习模式不能混入全职岗位")
    if job.get("company") in profile.get("excluded_companies", []):
        rejected.append("学生明确排除该公司")
    if job.get("industry") and job["industry"] in profile.get("excluded_industries", []):
        rejected.append("学生明确排除该行业")
    checks = job.get("checks") or {}
    for key in mode_checks(profile):
        check = checks.get(key) or {}
        if check.get("status") == "fail":
            rejected.append("硬条件不符：" + key)
        elif check.get("status") != "pass" or not check.get("quote") or not web_url(check.get("source_url")):
            pending.append("缺少硬条件通过证据：" + key)
    extra_rejected, extra_pending = mode_issues(profile, job)
    rejected.extend(extra_rejected)
    pending.extend(extra_pending)
    if job.get("graduation_window") is not None:
        try:
            window = job["graduation_window"]
            lower, upper = date_span(window["start"])[0], date_span(window["end"])[1]
            first, last = date_span(profile.get("graduation_date"))
            if lower > upper:
                raise ValueError("毕业窗口起止倒置")
            if last < lower or first > upper:
                rejected.append("毕业年月不在官方窗口内")
            elif first < lower or last > upper:
                pending.append("毕业月份落在窗口边界，需要确认具体毕业日")
        except (ValueError, TypeError, KeyError):
            pending.append("官方毕业窗口无法解析")
    try:
        deadline = deadline_time(job.get("deadline"))
        if deadline and now > deadline:
            rejected.append("已过官方截止时间")
    except (ValueError, TypeError):
        pending.append("截止时间无法解析或时区不明")
    context = str(job.get("job_id") or job.get("url") or "")
    for name in ("availability", "application"):
        observation = job.get(name) or {}
        state = observation.get("status")
        is_blocked = state in {"blocked", "error"} or observation.get("http_status") in BLOCKED_HTTP
        if is_blocked:
            blocked.append(name + " 暂时无法核验；不能据此判断下架")
        scoped = observation.get("context") == context
        if name == "availability":
            scoped = scoped and observation.get("scope") in {"job_detail", "job_listing"}
        if not scoped:
            pending.append(name + " 未限定到当前岗位；首页/相关推荐/仅URL变化不算证据")
        elif not is_blocked and (state == "closed" or CLOSED.search(str(observation.get("text") or ""))):
            rejected.append(name + " 明确停止招聘或不存在")
        chat = name == "application" and observation.get("route") == "chat"
        allowed = {"active"} if name == "availability" else ({"chat_available", "login_required"} if chat else {"form", "login_required", "consent_required"})
        if state not in allowed and not is_blocked and state != "closed":
            pending.append(name + " 缺少有效状态")
        if name == "application":
            if chat and not has_text(observation.get("recruiter_id")):
                pending.append("沟通入口未识别当前岗位招聘者；登录回跳不能替代招聘者证据")
            visible_chat = (chat and state == "chat_available" and observation.get("entry_method") == "visible_control"
                            and observation.get("control_enabled") is True and has_text(observation.get("recruiter_id")))
            direct_open = (observation.get("entry_method") == "direct_url"
                           and observation.get("opened") is True and web_url(observation.get("final_url")))
            if not visible_chat and observation.get("clicked") is not True and not direct_open:
                pending.append("application 未记录实际点击或打开申请入口")
            if chat and state == "chat_available" and not visible_chat:
                pending.append("缺少当前岗位可用沟通控件及招聘者标识；不以发送消息验证")
        if not str(observation.get("text") or "").strip():
            pending.append(name + " 缺少实际观察内容")
        try:
            age = now - checked_time(observation.get("checked_at"))
            if age > timedelta(hours=max_age_hours) or age < -timedelta(minutes=5):
                pending.append(name + " 核验过期或时间异常，需重新访问")
        except (ValueError, TypeError):
            pending.append(name + " 缺少带时区的实际核验时间")
        try:
            artifact = Path(str(observation.get("evidence_file") or ""))
            if not artifact.is_file() or artifact.stat().st_size == 0:
                pending.append(name + " 证据文件缺失或为空")
        except OSError:
            pending.append(name + " 证据文件不可读取")
    review_rejected, review_pending = review_issues(profile, job, now, max_age_hours,
                                                   sources if sources is not None else resume_sources(profile))
    rejected.extend(review_rejected)
    pending.extend(review_pending)
    status = "rejected" if rejected else "blocked" if blocked else "pending" if pending else "ready"
    return status, rejected + blocked + pending


def audit_jobs(profile, jobs, existing, *, now=None, max_age_hours=24, max_per_company=3, mode="add"):
    now = now or datetime.now(TZ)
    if now.tzinfo is None or max_age_hours <= 0 or max_per_company < 1 or mode not in {"add", "audit"}:
        raise ValueError("核验时区/时效/公司上限/模式无效")
    if not isinstance(profile, dict) or not isinstance(jobs, list) or not isinstance(existing, list):
        raise ValueError("画像必须为对象；岗位和历史必须为对象数组")
    if any(not isinstance(row, dict) for row in jobs + existing):
        raise ValueError("岗位和历史数组中必须都是对象")
    sources = resume_sources(profile)
    errors = profile_errors(profile) + sources[0]
    observed_counts, observed_names, observed_keys = Counter(), {}, set()
    for row in jobs if mode == "audit" else existing:
        key, company = job_key(row), company_key(row)
        if key and company and key not in observed_keys:
            observed_keys.add(key)
            observed_counts[company] += 1
            observed_names[company] = row.get("company") or company
    company_over_limit = {observed_names[k]: n for k, n in observed_counts.items() if n > max_per_company}
    seen = {job_key(row) for row in existing if job_key(row)} if mode == "add" else set()
    counts = Counter()
    # Count distinct historical jobs, without modifying historical rows.
    historical_seen = set()
    for row in existing if mode == "add" else []:
        key = job_key(row)
        if not company_key(row) or not key:
            errors.append("历史快照未标准化，公司或职位唯一键缺失")
        elif key not in historical_seen:
            counts[company_key(row)] += 1
            historical_seen.add(key)
    results, ready = [], []
    for index, job in enumerate(jobs):
        status, reasons = check_job(profile, job, now, max_age_hours, sources)
        if errors and status == "ready":
            status, reasons = "pending", list(dict.fromkeys(errors))
        key, company = job_key(job), company_key(job)
        if key and key in seen:
            status, reasons = "rejected", reasons + ["与历史或本轮岗位重复"]
        elif key:
            seen.add(key)
        if status == "ready" and counts[company] >= max_per_company:
            status, reasons = "rejected", ["同一学生同一公司累计超过上限；历史不删除"]
        if status == "ready":
            counts[company] += 1
            approved = dict(job)
            approved["selected_cities"] = [c for c in job["cities"] if c in profile["cities"]]
            approved["quality_gate"] = {
                "status": "ready", "checked_at": now.isoformat(),
                "profile_hash": fingerprint(profile), "job_hash": fingerprint(job),
                "scope": "conditions_entry_inspection_and_resume_jd_review",
                "search_mode": search_mode(profile), "application_route": job.get("application", {}).get("route", "form"),
                "delivery_verified": False,
            }
            ready.append(approved)
        results.append({"index": index, "company": job.get("company"), "title": job.get("title"),
                        "job_key": key, "record_id": job.get("record_id"), "status": status, "reasons": reasons,
                        "final_review_summary": (job.get("final_review") or {}).get("summary")
                        if isinstance(job.get("final_review"), dict) else None})
        if mode == "audit" and observed_counts[company] > max_per_company:
            results[-1]["company_count_issue"] = {"count": observed_counts[company], "limit": max_per_company}
    summary = {s: sum(r["status"] == s for r in results) for s in ("ready", "pending", "blocked", "rejected")}
    summary["total"] = len(jobs)
    return {"checked_at": now.isoformat(), "mode": mode, "profile_errors": list(dict.fromkeys(errors)),
            "company_over_limit": company_over_limit,
            "summary": summary, "results": results, "ready_jobs": ready}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--jobs", required=True, type=Path)
    parser.add_argument("--existing", required=True, type=Path, help="标准化历史快照；首次新表显式传入 []")
    parser.add_argument("--mode", choices=["add", "audit"], default="add")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--ready-output", type=Path)
    parser.add_argument("--now", help="仅用于可复现测试；实际交付省略")
    args = parser.parse_args()
    try:
        load = lambda path: json.loads(path.read_text(encoding="utf-8-sig"))
        report = audit_jobs(load(args.profile), load(args.jobs), load(args.existing),
                            now=checked_time(args.now) if args.now else None, mode=args.mode)
        ready = report.pop("ready_jobs")
        if args.ready_output:
            args.ready_output.write_text(json.dumps(ready, ensure_ascii=False, indent=2) + "\n")
        text = json.dumps(report, ensure_ascii=False, indent=2)
        if args.report:
            args.report.write_text(text + "\n")
        print(text)
        return 0 if report["summary"]["ready"] == report["summary"]["total"] and not report["profile_errors"] else 1
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(json.dumps({"error": str(exc), "ready": 0}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
