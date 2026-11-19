# billkit 目录规范

> 状态：Active
> 最后核验：2026-11-20

单一事实源：git 历史即归档，工作树不保留重复目录。

```text
bill-review/
├── src/              核心 CLI（billkit：清洗/分类/导出）
├── web/              本地前端（review.html / dashboard.html，纯前端、零依赖）
├── sample/           合成示例数据（仅此入库，供开箱演示）
├── tests/            测试
├── scripts/          校验与编排脚本
├── docs/             文档（编号分区，见 docs/README.md）
├── data/             真实账单（.gitignore，绝不入库）
├── build/            生成产物（.gitignore）
├── requirements.txt
├── LICENSE
└── README.md
```

## 所有权
| Concern | 维护源 | 消费方 |
| --- | --- | --- |
| 分类/导出逻辑 | `src/billkit.py` | CLI、web 复核 |
| 复核/看板界面 | `web/` | 本地浏览器打开 |
| 字段与导出契约 | `docs/03-reference/` | 开发与贡献者 |
| 真实账单 | `data/`（本地） | 不上传、不入库 |

禁止把真实账单、生成产物提交进仓库；禁止在 `sample/` 放真实数据。
