#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai_classify — 对「待分类/新商户」批量预分类，降低人工复核率。

支持两种后端（OpenAI 兼容 / Ollama），provider 显式指定：
  --provider openai  走 PP 网关（默认读全局变量 PP_LLM_BASE / PP_LLM_KEY / PP_LLM_MODEL）
  --provider ollama  走本机 Ollama（默认 127.0.0.1:11434 / qwen2.5:3b）

用法:
  # PP 网关（推荐，读全局环境变量）
  python3 src/ai_classify.py --provider openai --classified build/classified.csv --out build/classified.csv --cache build/ai_cache_pp.json
  # 本机 Ollama
  python3 src/ai_classify.py --provider ollama --classified build/classified.csv --out build/classified.csv --cache build/ai_cache.json
"""
import argparse, csv, json, os, re, sys, urllib.request
from collections import Counter

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

def _post(url, body, headers, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'),
                                 headers=dict({'Content-Type': 'application/json'}, **headers))
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def call_ollama(endpoint, model, prompt, timeout=180):
    d = _post(endpoint.rstrip('/') + '/api/chat',
              {"model": model, "stream": False,
               "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": prompt}],
               "options": {"temperature": 0}}, {}, timeout)
    return d.get('message', {}).get('content', '')

def call_openai(base, key, model, prompt, timeout=180):
    d = _post(base.rstrip('/') + '/chat/completions',
              {"model": model, "temperature": 0,
               "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": prompt}]},
              {'Authorization': 'Bearer ' + (key or '')}, timeout)
    return d['choices'][0]['message']['content']

def parse_json_array(text):
    text = (text or '').strip()
    text = re.sub(r'^```(json)?', '', text); text = re.sub(r'```$', '', text).strip()
    m = re.search(r'\[.*\]', text, re.S)
    if not m: return []
    try: return json.loads(m.group(0))
    except Exception: return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--classified', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--provider', default='ollama', choices=['ollama', 'openai'])
    ap.add_argument('--endpoint', default='')
    ap.add_argument('--model', default='')
    ap.add_argument('--key', default='')
    ap.add_argument('--cache', default=None)
    ap.add_argument('--min-conf', type=float, default=0.6)
    ap.add_argument('--batch', type=int, default=12)
    ap.add_argument('--limit', type=int, default=0)
    ns = ap.parse_args()

    if ns.provider == 'openai':
        endpoint = ns.endpoint or os.environ.get('PP_LLM_BASE', '')
        model = ns.model or os.environ.get('PP_LLM_MODEL', '')
        key = ns.key or os.environ.get('PP_LLM_KEY', '')
        if not endpoint or not model:
            sys.exit('缺 PP 网关配置：请设 PP_LLM_BASE / PP_LLM_MODEL（或 --endpoint/--model）')
    else:
        endpoint = ns.endpoint or 'http://127.0.0.1:11434'
        model = ns.model or 'qwen2.5:3b'; key = ''

    with open(ns.classified, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys())

    info = {}
    for r in rows:
        if r.get('needs_review') != '1': continue
        cp = (r.get('counterparty') or '').strip()
        if not cp: continue
        d = info.setdefault(cp, {'name': cp, 'cats': Counter(), 'notes': Counter()})
        if r.get('category'): d['cats'][r['category']] += 1
        if r.get('note'): d['notes'][r['note']] += 1
    names = sorted(info.keys(), key=lambda k: -sum(info[k]['cats'].values()))
    if ns.limit: names = names[:ns.limit]
    items = [{'name': n,
              'category': info[n]['cats'].most_common(1)[0][0] if info[n]['cats'] else '',
              'note': info[n]['notes'].most_common(1)[0][0] if info[n]['notes'] else ''} for n in names]
    print(f"provider={ns.provider} model={model} 待分类商户: {len(items)}")

    cache = {}
    if ns.cache and os.path.exists(ns.cache):
        cache = json.load(open(ns.cache, encoding='utf-8'))
    todo = [it for it in items if it['name'] not in cache]
    print(f"需查询(缓存外): {len(todo)}")
    call = (lambda p: call_openai(endpoint, key, model, p)) if ns.provider == 'openai' else (lambda p: call_ollama(endpoint, model, p))
    for start in range(0, len(todo), ns.batch):
        chunk = todo[start:start+ns.batch]
        try:
            arr = parse_json_array(call(build_prompt(chunk)))
        except Exception as e:
            print("  batch err:", e); arr = []
        ok = 0
        for obj in arr:
            try:
                idx = int(obj.get('i')) - 1
                if 0 <= idx < len(chunk):
                    l1 = (obj.get('l1') or '').strip()
                    if l1 not in TAX: l1 = '其他'
                    cache[chunk[idx]['name']] = {'l1': l1, 'l2': (obj.get('l2') or '').strip(),
                                                 'confidence': float(obj.get('confidence') or 0.5)}
                    ok += 1
            except Exception:
                pass
        print(f"  批次 {start//ns.batch+1}: {ok}/{len(chunk)}")
        if ns.cache:
            json.dump(cache, open(ns.cache, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    before = sum(1 for r in rows if r.get('needs_review') == '1')
    applied = 0
    for r in rows:
        if r.get('needs_review') != '1': continue
        c = cache.get((r.get('counterparty') or '').strip())
        if c and c.get('confidence', 0) >= ns.min_conf:
            r['purpose_l1'] = c['l1']; r['purpose_l2'] = c.get('l2', '')
            r['confidence'] = f"{c['confidence']:.2f}"; r['classify_by'] = 'ai:' + ns.provider
            r['needs_review'] = '0'; applied += 1
    after = sum(1 for r in rows if r.get('needs_review') == '1')
    with open(ns.out, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader()
        for r in rows: w.writerow(r)
    print(json.dumps({'before_review': before, 'ai_applied': applied, 'after_review': after,
                      'review_pct_after': round(after*100/len(rows), 1)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
