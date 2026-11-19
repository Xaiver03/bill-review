# billkit 文档中心

> 状态：Active
> 最后核验：2026-11-20

这里是本工程文档的**唯一入口**。文档按「长期架构 / 使用流程 / 参考资料 / 操作指南 / 项目记录 / 计划」组织；同一事实只在一个权威文档维护，其余用链接引用；被取代的材料只留 Git 历史。

## 先从这里开始
| 需求 | 权威入口 |
| --- | --- |
| 了解系统设计与信息架构 | [架构总览](01-architecture/README.md) |
| 信息架构与命名/分层规范 | [信息架构规范](01-architecture/information-architecture.md) |
| 分类算法怎么工作 | [分类设计](01-architecture/classification.md) |
| AI 预分类（本地模型） | [AI 预分类](01-architecture/ai-classification.md) |
| 分类→复核→导出怎么走 | [复核闭环](02-workflow/review-loop.md) |
| 输入输出字段 | [字段规范](03-reference/schema.md) |
| 导出到 木木/Firefly/beancount | [导出目标映射](03-reference/export-targets.md) |
| 安装 / 运行 / 参与贡献 | [操作指南](04-guides/install.md) |
| 项目实现记录 | [项目记录](05-project/README.md) |
| 下一步计划 | [路线图](plans/roadmap.md) |

## 信息结构
```text
docs/
├── 01-architecture/   长期有效的设计、信息架构与算法边界
├── 02-workflow/       使用流程（分类/复核/导出）
├── 03-reference/      参考资料（字段、导出目标映射）
├── 04-guides/         操作指南（安装/运行/贡献）
├── 05-project/        有日期的项目实现与验收记录
└── plans/             尚未完成的实施计划
```

## 状态
| 状态 | 含义 |
| --- | --- |
| Active | 当前权威事实，改实现必须同步 |
| Draft | 评审中，不作已实现依据 |
| Planned | 已批准未完成 |
| Superseded | 已被取代，从工作树删除、靠 Git 历史 |

维护规则见 [DOCUMENTATION_STANDARD.md](DOCUMENTATION_STANDARD.md)。
