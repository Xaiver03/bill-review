# AI 预分类（本机 Ollama / PP 网关）

> 状态：Active · 最后核验：2026-11-20 · 权威实现：`src/ai_classify.py`

在规则分类之后，对 `needs_review=1` 且**对手方非空**的行，按商户去重、批量打标，写回 `classified.csv`（`classify_by=ai:<provider>`，`confidence<min-conf` 仍留复核）。

## 两种后端（`--provider`）
| provider | 端点 | 模型 | 说明 |
| --- | --- | --- | --- |
| `ollama` | `127.0.0.1:11434` | `qwen2.5:3b`（默认） | 本机、免费、数据不出机 |
| `openai` | `$PP_LLM_BASE` | `$PP_LLM_MODEL` | OpenAI 兼容的 **PP 网关**（读全局环境变量） |

PP 网关全局变量：`PP_LLM_BASE` / `PP_LLM_KEY` / `PP_LLM_MODEL`（存于 `~/.config/pp-gateway/env`，0600）。

## 实测（6,533 条）
- Ollama：复核 1190(18.2%) → 690(10.6%)
- PP 网关补跑：690 → **682(10.4%)**
- 剩余约 650 行为**无对手方的银行流水**（AI 无法归类，留人工）。

命令见 [运行指南](../04-guides/run.md)。

## 后端对比结论（2026-11-20，6,533 条实测）
| 版本 | 复核行 | 复核率 |
|---|---|---|
| 规则基线 | 1190 | 18.2% |
| Ollama qwen2.5:3b（0.6） | 684 | 10.5% |
| PP 网关 kimi-k3.1-pro（接受全部） | **650** | **10.0%** |
- L1 一致率 40.1%；金标准抽检（34 商户）：Ollama 32.4% vs **PP 76.5%**。
- 结论：**默认 PP 网关**（更准；复核更低）。Ollama 仅离线兜底。详见 [后端对比记录](../05-project/2026-11-20-provider-compare.md)。
