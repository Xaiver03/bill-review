#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_memory — 项目记忆体系校验。

检查：
1. 仓库根存在 AGENTS.md，且含工作原则与记忆索引入口；
2. docs/06-memory/README.md 存在，其相对 .md 链接全部可解析；
3. docs/06-memory/ 下每个非 README 的记忆文档，前 600 字内含「状态」元数据；
4. 索引完整性：docs/06-memory/ 下每个非 README 的 .md 都被 README.md 链接覆盖。
退出码 1 表示有问题。
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEM = os.path.join(ROOT, 'docs', '06-memory')
AGENTS = os.path.join(ROOT, 'AGENTS.md')
LINK = re.compile(r'\]\(([^)]+)\)')

def rel_targets(mdpath):
    txt = open(mdpath, encoding='utf-8').read()
    out = []
    for m in LINK.finditer(txt):
        t = m.group(1).strip()
        if t.startswith(('http://', 'https://', '#')):
            continue
        t = t.split('#')[0]
        if not t.endswith('.md'):
            continue
        out.append((t, os.path.normpath(os.path.join(os.path.dirname(mdpath), t))))
    return out

def main():
    errors = []
    # 1. AGENTS.md 存在且含关键内容
    if not os.path.isfile(AGENTS):
        errors.append('缺少仓库根 AGENTS.md')
    else:
        txt = open(AGENTS, encoding='utf-8').read()
        for kw in ('许愿式编程', 'docs/06-memory/README.md', '记忆'):
            if kw not in txt:
                errors.append(f'AGENTS.md 缺少关键内容: {kw}')
    # 2. 记忆中心 README 存在且链接可解析
    mreadme = os.path.join(MEM, 'README.md')
    if not os.path.isfile(mreadme):
        errors.append('缺少 docs/06-memory/README.md')
        print('❌ 记忆校验失败：')
        for e in errors:
            print('  -', e)
        sys.exit(1)
    for raw, absp in rel_targets(mreadme):
        if not os.path.exists(absp):
            errors.append(f'记忆索引断链: {raw}')
    # 3. 每个非 README 记忆文档有状态元数据
    mem_files = []
    for base, _, files in os.walk(MEM):
        for f in sorted(files):
            if not f.endswith('.md') or f == 'README.md':
                continue
            p = os.path.join(base, f)
            mem_files.append(p)
            head = open(p, encoding='utf-8').read(600)
            if '状态' not in head:
                errors.append(f'记忆文档缺状态元数据: {os.path.relpath(p, ROOT)}')
    # 4. 索引完整性：每个记忆文档都被 README 链接
    linked = {os.path.normpath(os.path.join(MEM, t)) for t, _ in rel_targets(mreadme)}
    for p in mem_files:
        if os.path.normpath(p) not in linked:
            errors.append(f'记忆索引未登记: {os.path.relpath(p, ROOT)}')
    if errors:
        print('❌ 记忆校验失败：')
        for e in errors:
            print('  -', e)
        sys.exit(1)
    print(f'✅ 记忆校验通过：AGENTS.md + {len(mem_files)} 篇记忆，索引完整、链接可解析')

if __name__ == '__main__':
    main()
