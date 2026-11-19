# 导出目标映射

> 状态：Active · 最后核验：2026-11-20

| 目标 | 产物 | 导入方式 |
| --- | --- | --- |
| 木木记账 | `mumu_import.xlsx`（14 列模板：账单时间/类型/分类/子分类/金额/账本/账户1…） | 木木模板导入 |
| Firefly III | `firefly.csv`（date,amount,description,category,source_account,…） | Data Importer 映射列 或 `/api/v1/transactions` |
| beancount | `beancount.bean`（含 open 指令，收支/转账科目） | `fava build/beancount.bean` |

类型映射：`expense→支出/withdrawal/Expenses:*`，`income→收入/deposit/Income:Income`，`neutral→转账/transfer/Assets:Transfer`。
