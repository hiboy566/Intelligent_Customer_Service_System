# Intelligent Customer Service System

用于记录智能客服模型的每次训练，包括配置、数据版本、指标和模型产物。

## 目录

- `configs/`：可复用训练配置。
- `training_runs/`：每次训练的独立记录。
- `datasets/`：允许公开的数据集或数据说明。
- `artifacts/`：模型权重、日志和评测结果。

## 客服数据集

`datasets/` 已准备 LLaMA-Factory Alpaca 格式的合成中文客服数据：

- 50 条 smoke test 数据；
- 500 条训练数据；
- 100 条校验数据。

数据覆盖 25 类常见电商客服意图，详情和使用方式见 `datasets/README.md`。可通过
`python scripts/generate_customer_service_datasets.py` 确定性地重新生成。

## 记录一次训练

1. 复制 `training_runs/TEMPLATE.md` 到 `training_runs/YYYY-MM-DD_run-name/README.md`。
2. 保存实际使用的配置、代码提交号、数据版本和环境信息。
3. 训练结束后补充指标、结论和模型产物路径。
4. 提交并推送到 GitHub。

## 大文件

模型权重由 Git LFS 管理，已覆盖 `*.safetensors`、`*.bin`、`*.pt`、`*.pth` 和 `*.ckpt`。

## 安全说明

这是公开仓库。数据、样本和权重提交前应确认许可证及隐私要求。真实密码、令牌、SSH 私钥和其他密钥不得提交；请只填写 `.env.example` 的副本，并将真实值保存在环境变量或密钥管理服务中。
