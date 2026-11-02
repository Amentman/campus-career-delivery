"""Validate system-only patches for existing collaboration records; no remote writes."""
import argparse
import json
from pathlib import Path
PROTECTED = frozenset({'负责人','状态','完成','备注','计划日期','优先级'})
ALLOWED = frozenset({'任务','工作类型','责任队列','建议下一步','原分工参考','时间线索','积压标记','结转次数','来源证据','完成标准','系统建议','资料截止','系统计划日','上次结转目标日','关闭依据','来源日期','继承状态','执行分区','执行顺序'})
def validate_patch(patch):
    if not isinstance(patch,dict) or not patch: raise ValueError('补丁必须是非空字段对象')
    denied=set(patch)-ALLOWED
    if denied: raise ValueError('禁止自动写入字段：'+'、'.join(sorted(denied)))
    return patch
def active_records(records):
    ids=[r['任务编号'] for r in records]
    if len(set(ids))!=len(ids): raise ValueError('任务编号重复，停止合并')
    return [r for r in records if r.get('完成') is False and r.get('继承状态') not in ('历史已完成',['历史已完成'])]
def carry_forward(records, historical_checked_ids=()):
    """Preserve manual values, excluding completion from any historical source."""
    closed=set(historical_checked_ids)|{r['任务编号'] for r in records if r.get('完成') is True}
    return [dict(r) for r in active_records(records) if r['任务编号'] not in closed]
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--patch',required=True);a=p.parse_args()
    print(json.dumps(validate_patch(json.loads(Path(a.patch).read_text())),ensure_ascii=False))
