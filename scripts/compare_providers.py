#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compare_providers — 对比两个 AI 后端（Ollama vs PP 网关）在账单分类上的表现。

输入：同一规则基线下生成的两份 classified（ollama / pp）+ 两个商户级缓存。
输出：compare.json / compare.md / gold_candidates.csv（供人工金标准抽检）。
"""
import argparse, csv, json, os
from collections import Counter, defaultdict

def read_cache(p):
    return json.load(open(p, encoding='utf-8')) if p and os.path.exists(p) else {}

def review_stats(path):
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
    rev = sum(1 for r in rows if r.get('needs_review') == '1')
    return len(rows), rev

def ai_conf(path):
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
    confs = [float(r['confidence']) for r in rows if str(r.get('classify_by','')).startswith('ai') and r.get('confidence')]
    return (round(sum(confs)/len(confs),3) if confs else None, len(confs))

def merchant_context(rule_path):
    ctx = {}
    for r in csv.DictReader(open(rule_path, encoding='utf-8-sig')):
        cp = (r.get('counterparty') or '').strip()
        if not cp: continue
        d = ctx.setdefault(cp, {'n': 0, 'cats': Counter(), 'notes': Counter()})
        d['n'] += 1
        if r.get('category'): d['cats'][r['category']] += 1
        if r.get('note'): d['notes'][r['note']] += 1
    return ctx

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rule', required=True)
    ap.add_argument('--ollama', required=True)
    ap.add_argument('--pp', required=True)
    ap.add_argument('--cache-ollama', required=True)
    ap.add_argument('--cache-pp', required=True)
    ap.add_argument('--out', required=True)
    ns = ap.parse_args()
    os.makedirs(ns.out, exist_ok=True)

    tot = review_stats(ns.rule)[0]
    res = {'total': tot}
    for name, path in [('rule', ns.rule), ('ollama', ns.ollama), ('pp', ns.pp)]:
        n, rev = review_stats(path)
        res[name] = {'review': rev, 'review_pct': round(rev*100/n, 1)}

    co, cp = read_cache(ns.cache_ollama), read_cache(ns.cache_pp)
    common = sorted(set(co) & set(cp))
    agree = [m for m in common if co[m].get('l1') == cp[m].get('l1')]
    res['merchants'] = {'ollama': len(co), 'pp': len(cp), 'common': len(common),
                        'agree': len(agree),
                        'agreement_pct': round(len(agree)*100/max(len(common),1), 1)}
    res['conf'] = {'ollama': ai_conf(ns.ollama)[0], 'pp': ai_conf(ns.pp)[0],
                   'ollama_ai_rows': ai_conf(ns.ollama)[1], 'pp_ai_rows': ai_conf(ns.pp)[1]}

    ctx = merchant_context(ns.rule)
    # 金标准候选：先分歧后一致，各取，带上下文
    disagree = [m for m in common if m not in agree]
    def row_of(m):
        c = ctx.get(m, {'n':0,'cats':Counter(),'notes':Counter()})
        return {'merchant': m,
                'l1_ollama': co[m].get('l1'), 'l2_ollama': co[m].get('l2',''), 'conf_ollama': co[m].get('confidence'),
                'l1_pp': cp[m].get('l1'), 'l2_pp': cp[m].get('l2',''), 'conf_pp': cp[m].get('confidence'),
                'rows': c['n'],
                'category': c['cats'].most_common(1)[0][0] if c['cats'] else '',
                'note': (c['notes'].most_common(1)[0][0] if c['notes'] else '')[:40],
                'agree': co[m].get('l1') == cp[m].get('l1')}
    cand = [row_of(m) for m in disagree[:22]] + [row_of(m) for m in agree[:12]]
    cand.sort(key=lambda r: (r['agree'], -r['rows']))
    with open(os.path.join(ns.out, 'gold_candidates.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=['merchant','l1_ollama','l2_ollama','conf_ollama','l1_pp','l2_pp','conf_pp','rows','category','note','agree','gold_l1'])
        w.writeheader()
        for r in cand:
            r['gold_l1'] = ''
            w.writerow(r)

    json.dump(res, open(os.path.join(ns.out, 'compare.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    md = ["# 后端对比（规则基线起）", "",
          "| 版本 | 复核行 | 复核率 |", "|---|---|---|",
          f"| 规则基线 | {res['rule']['review']} | {res['rule']['review_pct']}% |",
          f"| + Ollama | {res['ollama']['review']} | {res['ollama']['review_pct']}% |",
          f"| + PP 网关 | {res['pp']['review']} | {res['pp']['review_pct']}% |", "",
          f"- 两模型覆盖商户：Ollama {res['merchants']['ollama']}，PP {res['merchants']['pp']}，共同 {res['merchants']['common']}",
          f"- 一致率：**{res['merchants']['agreement_pct']}%**（{res['merchants']['agree']}/{res['merchants']['common']}）",
          f"- 平均置信度：Ollama {res['conf']['ollama']}，PP {res['conf']['pp']}"]
    open(os.path.join(ns.out, 'compare.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    print(json.dumps({k: res[k] for k in ['rule','ollama','pp','merchants','conf']}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
