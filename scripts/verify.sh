#!/usr/bin/env bash
# 本地自检：文档结构 + 单元测试 + sample 全流程 + beancount 校验
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== 文档结构 =="; python3 scripts/verify_docs.py
echo "== 单元测试 =="; python3 tests/test_billkit.py
echo "== sample 全流程 =="; OUT=$(mktemp -d); python3 src/billkit.py all --input sample/ledger.sample.csv --out "$OUT" >/dev/null
echo "== beancount 校验 =="
python3 - "$OUT/beancount.bean" <<'PY'
import sys
from beancount import loader
e, err, _ = loader.load_file(sys.argv[1])
print('beancount errors:', len(err)); assert len(err) == 0
PY
echo "ALL GREEN"
