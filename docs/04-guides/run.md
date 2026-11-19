# 运行

> 状态：Active · 最后核验：2026-11-20

```bash
# 全流程（分类+导出）
python3 src/billkit.py all --input sample/ledger.sample.csv --out build/
# 只分类 / 只导出
python3 src/billkit.py classify --input data/账单.csv --out build/
python3 src/billkit.py export --classified build/classified.csv --out build/
# AI 预分类（可选，需本机 Ollama）
python3 src/ai_classify.py --classified build/classified.csv --out build/classified.csv --cache build/ai_cache.json
# 自检
bash scripts/verify.sh
```
