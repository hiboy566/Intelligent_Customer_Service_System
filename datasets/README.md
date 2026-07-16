# 客服训练数据

本目录包含可直接注册到 LLaMA-Factory 的 Alpaca 格式中文客服数据。

| 数据集 | 数量 | 用途 |
| --- | ---: | --- |
| `customer_service_smoke.json` | 50 | 快速验证数据加载、模板和训练链路 |
| `customer_service_train.json` | 500 | SFT 训练集 |
| `customer_service_validation.json` | 100 | 训练期间校验和模型选择 |

三个集合均覆盖 25 类客服意图。每类分别包含 2 条 smoke、20 条训练和 4 条校验样本，集合之间的用户措辞、上下文和合成订单号互不重复。

数据均为脚本生成的合成内容，不包含真实用户隐私。订单号以 `TEST-` 开头，不应被当作真实订单。

## LLaMA-Factory 使用方式

将 `dataset_dir` 指向本目录，并使用 `dataset_info.json` 中的名称：

```yaml
dataset_dir: ./datasets
dataset: customer_service_train
eval_dataset: customer_service_validation
```

首次训练前可将 `dataset` 临时改为 `customer_service_smoke`，用于 smoke test。

## 重新生成

```bash
python scripts/generate_customer_service_datasets.py
python scripts/validate_datasets.py
```

生成过程是确定性的。修改生成脚本后，应重新执行校验并记录数据文件的哈希值。
