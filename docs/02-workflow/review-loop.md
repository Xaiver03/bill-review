# 复核闭环（分类 → 人工 → 导出）

> 状态：Active · 最后核验：2026-11-20

1. 生成：`python3 src/billkit.py all --input data/xxx.csv --out build/`
2. 复核：浏览器打开 `web/review.html`，选 `build/classified.csv`；左栏按对手方批量打分类，右表微调；点「导出已复核 CSV」得 `classified_corrected.csv`。
3. 重导出：`python3 src/billkit.py export --classified classified_corrected.csv --out build/`
4. 看板：`web/dashboard.html` 选 `build/classified.csv`。
5. 导账：`build/mumu_import.xlsx` / `build/firefly.csv` / `build/beancount.bean`。

复核只处理 `needs_review=1` 的行；按对手方批量套用把上千行压到几十个对象。
