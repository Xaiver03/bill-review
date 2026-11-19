#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_docs — 文档结构校验（仿 SSOS verify:docs-structure）。

检查：
1. docs/README.md 里的相对 .md 链接都能解析到真实文件；
2. 每个 docs/**/*.md（README 除外可无）标题下有「> 状态」元数据；
3. docs 编号分区目录存在；
4. 全库 docs markdown 内的相对 .md 链接可解析。
退出码 1 表示有问题。
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
ZONES = ['01-architecture', '02-workflow', '03-reference', '04-guides', '05-project', 'plans']
LINK = re.compile(r'\]\(([^)]+)\)')

def md_files():
    for base, _, files in os.walk(DOCS):
        for f in files:
            if f.endswith('.md'):
                yield os.path.join(base, f)

def rel_targets(mdpath):
    txt = open(mdpath, encoding='utf-8').read()
    out = []
    for m in LINK.finditer(txt):
        t = m.group(1).strip()
        if t.startswith(('http://', 'https://', '#')): continue
        t = t.split('#')[0]
        if not t.endswith('.md'): continue
        out.append((t, os.path.normpath(os.path.join(os.path.dirname(mdpath), t))))
    return out

def main():
    errors = []
    # 1 分区存在
    for z in ZONES:
        if not os.path.isdir(os.path.join(DOCS, z)):
            errors.append(f'缺少分区目录 docs/{z}/')
    # 2 每篇有状态
    for md in sorted(md_files()):
        if os.path.basename(md) == 'README.md':
            continue
        head = open(md, encoding='utf-8').read(600)
        if '状态' not in head:
            errors.append(f'缺状态元数据: {os.path.relpath(md, ROOT)}')
    # 3 链接可解析
    existing = {os.path.normpath(p) for p in md_files()}
    for md in sorted(md_files()):
        for raw, absp in rel_targets(md):
            if not os.path.exists(absp):
                errors.append(f'断链: {os.path.relpath(md, ROOT)} -> {raw}')
    if errors:
        print('❌ 文档校验失败：')
        for e in errors: print('  -', e)
        sys.exit(1)
    print(f'✅ 文档校验通过：{len(list(md_files()))} 篇，{len(ZONES)} 个分区，链接全部可解析')

if __name__ == '__main__':
    main()
