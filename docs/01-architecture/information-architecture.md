# 信息架构规范（billkit）

> 状态：Active · 最后核验：2026-11-20
> 借鉴：创业OS `docs/01-core/information-architecture.md` + `DOCUMENTATION_STANDARD.md`

## 一、三层分离（代码 / 数据 / 产物）
- **代码与文档**：进仓库、可公开（`src/ web/ docs/ sample/ tests/ scripts/`）。
- **真实数据**：只在本地 `data/`，`.gitignore` 排除，绝不入库、不上传。
- **生成产物**：只在本地 `build/`，可随时重跑再生，不入库。
单一事实源：同一内容只存在一处，需要复用用生成或链接，不手工同步副本。

## 二、目录按功能分区、编号排序
`docs/01-architecture` `02-workflow` `03-reference` `04-guides` `05-project` `plans`。
新增一类文档先归入既有分区；确需新分区用两位数编号，README 表格同步更新。

## 三、索引优先、可校验
`docs/README.md` 是唯一入口；每个分区一个活动入口；文档带「状态 / 最后核验 / 权威实现」。删除或移动文档必须同步修索引与相对链接。

## 四、界面 IA（两个本地页面）
- `review.html`：主任务=**批量确认分类**。左栏按对手方批量套用，右表逐行微调，导出在页头。
- `dashboard.html`：主任务=**看收支结构与趋势**。指标卡在上，图表为主区。
- 一页一主任务；次级动作（筛选、排序、导出）不抢主区。

## 五、历史只留 Git
被取代的文档/版本从工作树删除，由 Git 历史保存；不建 `archive/ backup/ old/` 副本目录。
