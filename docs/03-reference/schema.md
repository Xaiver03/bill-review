# 输入 / 输出字段

## 输入（原始账本 CSV）
| 字段 | 说明 |
|---|---|
| datetime | 交易时间，YYYY-MM-DD HH:MM:SS |
| amount | 金额（正数，方向看 type） |
| type | expense / income / neutral |
| counterparty | 对手方（商户/个人） |
| category | 源平台给的交易类型（可空） |
| note | 备注 |
| source | wechat / alipay / icbc / cmb |
| payment_method | 支付方式（含卡号后四位等） |

## 输出（classified.csv 追加字段）
| 字段 | 说明 |
|---|---|
| purpose_l1 | 用途一级分类（见 TAXONOMY） |
| purpose_l2 | 用途二级分类 |
| confidence | 置信度 0–1 |
| classify_by | type/cat/refund/transfer/invest/rule/prior/none |
| needs_review | 1=需人工复核 |
| account | 归一化账户名 |

TAXONOMY：餐饮 交通出行 购物日用 居住 生活服务 娱乐休闲 医疗健康 教育学习 旅游住宿 人情往来 金融保险 投资理财 转账还款 收入 退款/冲正 其他

## 输出（classified.csv 追加）
purpose_l1 / purpose_l2 / confidence / classify_by / needs_review / account（详见 architecture/classification.md）。
