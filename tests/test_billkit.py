#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最小自检：跑通 sample 的分类与导出，并校验产物存在。"""
import os, sys, subprocess, tempfile, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'billkit.py')
SAMPLE = os.path.join(ROOT, 'sample', 'ledger.sample.csv')

def run(args):
    return subprocess.run([sys.executable, SRC] + args, capture_output=True, text=True)

def main():
    out = tempfile.mkdtemp(prefix='billkit_test_')
    r = run(['all', '--input', SAMPLE, '--out', out])
    assert r.returncode == 0, r.stderr
    stats = json.load(open(os.path.join(out, 'stats.json'), encoding='utf-8'))
    assert stats['total'] > 0
    assert stats['auto'] + stats['review'] == stats['total']
    for f in ['classified.csv', 'review_queue.csv', 'beancount.bean', 'firefly.csv']:
        assert os.path.exists(os.path.join(out, f)), 'missing ' + f
    print('OK total=%d auto=%d review=%d' % (stats['total'], stats['auto'], stats['review']))

if __name__ == '__main__':
    main()
