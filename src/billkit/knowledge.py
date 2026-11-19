# -*- coding: utf-8 -*-
"""商户分类知识库：可移植的 merchant -> {l1,l2,count}。

用途：把用户每次人工复核沉淀为不随批次丢失的先验，使下一批自动率单调上升。
文件为纯 JSON，git 友好，可导出/分享。
"""
import json, os

REQUIRED_KEYS = ('l1', 'l2', 'count')


def load_knowledge(path):
    if not path:
        return {}
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    # 兼容 {"merchants": {...}} 或直接映射
    if isinstance(data, dict) and 'merchants' in data and isinstance(data['merchants'], dict):
        return data['merchants']
    if isinstance(data, dict):
        return data
    return {}


def save_knowledge(knowledge, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
    payload = {'version': 1, 'merchants': knowledge}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=1, sort_keys=True)
    return path


def learn_from_rows(corrected_rows, existing=None):
    """把已复核的 classified（needs_review 已消解）合并进知识库。

    只吸收有对手方、且最终分类明确（purpose_l1 非空且非“其他”）的行。
    同一商户取出现最多的 (l1,l2) 作为知识；count 累计该商户被确认的次数。
    """
    from collections import Counter
    existing = dict(existing or {})
    tally = {}
    for r in corrected_rows:
        cp = (r.get('counterparty') or '').strip()
        l1 = (r.get('purpose_l1') or '').strip()
        l2 = (r.get('purpose_l2') or '').strip()
        if not cp or not l1 or l1 == '其他':
            continue
        # 只学“已被确认”的行：needs_review 为 0，或显式来自复核结果
        tally.setdefault(cp, Counter())[(l1, l2)] += 1
    for cp, cnt in tally.items():
        (l1, l2), n = cnt.most_common(1)[0]
        prev = existing.get(cp) or {}
        prev_count = int(prev.get('count', 0) or 0)
        # 若新证据与旧知识冲突，以累计票数多者为准（保留稳健性）
        if prev and (prev.get('l1') != l1 or prev.get('l2', '') != l2):
            # 旧知识 count 视作同等票数一并比较
            if prev_count >= n:
                existing[cp] = {'l1': prev.get('l1'), 'l2': prev.get('l2', ''),
                                'count': prev_count + n}
                continue
        existing[cp] = {'l1': l1, 'l2': l2, 'count': prev_count + n}
    return existing
