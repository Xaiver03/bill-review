#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai_classify — 本地 Ollama 对「待分类/新商户」批量预分类，降低人工复核率。

只处理 needs_review=1 且对手方非空的行；按商户去重后批量问本地模型，结果带缓存。
用法:
  python3 src/ai_classify.py --classified build/classified.csv --out build/classified.csv \
      --endpoint http://127.0.0.1:11434 --model qwen2.5:3b --cache build/ai_cache.json --min-conf 0.6
"""
import argparse, csv, json, os, re, sys, urllib.request
from collections import Counter, defaultdict

TAX = ['餐饮','交通出行','购物日用','居住','生活服务','娱乐休闲','医疗健康','教育学习',
       '旅游住宿','人情往来','金融保险','投资理财','转账还款','收入','退款/冲正','其他']

SYS = "你是中文个人记账的分类助手。只输出 JSON 数组，不要任何解释或代码块标记。"

def build_prompt(items):
    lines = []
    for i, m in enumerate(items, 1):
        ctx = m['name']
        if m.get('category'): ctx += " | 类型:" + m['category']
        if m.get('note'): ctx += " | 备注:" + m['note'][:30]
        lines.append(f"{i}. {ctx}")
    return ("一级类别只能从这些里选：" + "、".join(TAX) + "。\n"
            "对下面每个商户给出 l1(必须属于上述类别)、l2(可选简短子类)、confidence(0到1的小数)。\n"
            "输入：\n" + "\n".join(lines) + "\n"
            '只输出 JSON 数组：[{"i":1,"l1":"餐饮","l2":"咖啡奶茶","confidence":0.8}, ...]')

def call_ollama(endpoint, model, prompt, timeout=180):
    body = {"model": model, "stream": False,
            "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": prompt}],
            "options": {"temperature": 0}}
    req = urllib.request.Request(endpoint.rstrip('/') + '/api/chat',
                                 data=json.dumps(body).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.load(r)
    return data.get('message', {}).get('content', '')

def parse_json_array(text):
    text = text.strip()
    text = re.sub(r'^```(json)?', '', text); text = re.sub(r'```$', '', text).strip()
    m = re.search(r'\[.*\]', text, re.S)
    if not m: return []
    try:
        return json.loads(m.group(0))
    except Exception:
        return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--classified', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--endpoint', default='http://127.0.0.1:11434')
    ap.add_argument('--model', default='qwen2.5:3b')
    ap.add_argument('--cache', default=None)
    ap.add_argument('--min-conf', type=float, default=0.6)
    ap.add_argument('--batch', type=int, default=20)
    ap.add_argument('--limit', type=int, default=0)
    ns = ap.parse_args()

    with open(ns.classified, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys())

    # 待复核且有对手方的商户 -> 代表性上下文
    info = {}
    for r in rows:
        if r.get('needs_review') != '1': continue
        cp = (r.get('counterparty') or '').strip()
        if not cp: continue
        d = info.setdefault(cp, {'name': cp, 'cats': Counter(), 'notes': Counter()})
        if r.get('category'): d['cats'][r['category']] += 1
        if r.get('note'): d['notes'][r['note']] += 1
    names = sorted(info.keys(), key=lambda k: -sum(info[k]['cats'].values()) - 1)
    if ns.limit: names = names[:ns.limit]
    items = []
    for n in names:
        d = info[n]
        items.append({'name': n,
                      'category': d['cats'].most_common(1)[0][0] if d['cats'] else '',
                      'note': d['notes'].most_common(1)[0][0] if d['notes'] else ''})
    print(f"待分类商户: {len(items)}")

    cache = {}
    if ns.cache and os.path.exists(ns.cache):
        cache = json.load(open(ns.cache, encoding='utf-8'))

    todo = [it for it in items if it['name'] not in cache]
    print(f"需查询(缓存外): {len(todo)}")
    for start in range(0, len(todo), ns.batch):
        chunk = todo[start:start+ns.batch]
        prompt = build_prompt(chunk)
        try:
            out = call_ollama(ns.endpoint, ns.model, prompt)
            arr = parse_json_array(out)
        except Exception as e:
            print("  batch err:", e); arr = []
        ok = 0
        for obj in arr:
            try:
                idx = int(obj.get('i')) - 1
                if 0 <= idx < len(chunk):
                    l1 = obj.get('l1', '').strip()
                    if l1 not in TAX: l1 = '其他'
                    cache[chunk[idx]['name']] = {'l1': l1, 'l2': (obj.get('l2') or '').strip(),
                                                 'confidence': float(obj.get('confidence') or 0.5)}
                    ok += 1
            except Exception:
                pass
        print(f"  批次 {start//ns.batch+1}: 得到 {ok}/{len(chunk)}")
        if ns.cache:
            json.dump(cache, open(ns.cache, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # 应用
    before = sum(1 for r in rows if r.get('needs_review') == '1')
    applied = 0
    for r in rows:
        if r.get('needs_review') != '1': continue
        cp = (r.get('counterparty') or '').strip()
        c = cache.get(cp)
        if c and c.get('confidence', 0) >= ns.min_conf:
            r['purpose_l1'] = c['l1']; r['purpose_l2'] = c.get('l2', '')
            r['confidence'] = f"{c['confidence']:.2f}"; r['classify_by'] = 'ai'
            r['needs_review'] = '0'; applied += 1
    after = sum(1 for r in rows if r.get('needs_review') == '1')

    with open(ns.out, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader()
        for r in rows: w.writerow(r)

    print(json.dumps({'before_review': before, 'ai_applied': applied, 'after_review': after,
                      'review_pct_before': round(before*100/len(rows),1),
                      'review_pct_after': round(after*100/len(rows),1)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
