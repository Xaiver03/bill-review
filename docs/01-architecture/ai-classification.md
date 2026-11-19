# AI 预分类（本地 Ollama）

> 状态：Active · 最后核验：2026-11-20 · 权威实现：`src/ai_classify.py`

在规则分类之后，对 `needs_review=1` 且**对手方非空**的行，按商户去重、批量问**本机 Ollama**（默认 `qwen2.5:3b`，`127.0.0.1:11434`），带缓存与置信度。

- 只把「商户名 / 类型 / 备注」发到本机，**不出本机**、不需 API Key。
- 结果写回 `classified.csv`：`classify_by=ai`，`confidence<min-conf` 仍留复核。
- 无对手方的银行流水（约 650 行）AI 无法归，保留人工。
- 实测：复核 **1190(18.2%) → 690(10.6%)**。

命令见 [运行指南](../04-guides/run.md)。
