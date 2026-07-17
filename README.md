# Intelligent Customer Service System

用于记录智能客服模型的每次训练，包括配置、数据版本、指标和模型产物。

## 目录

- `configs/`：可复用训练配置。
- `training_runs/`：每次训练的独立记录。
- `datasets/`：允许公开的数据集或数据说明。
- `artifacts/`：模型权重、日志和评测结果。
- `models/`：本地 adapter 文件。
- `service/`：FastAPI + PyTorch QLoRA 推理接口。
- `mastra-agent/`：调用 QLoRA 接口并使用 mock 后端 tools 的 Mastra Agent。

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

## QLoRA 推理接口

本地 adapter 位于 `models/qwen3-vl-8b-qlora-train-v1/`。服务会以 4-bit NF4
加载 Qwen3-VL-8B-Instruct 基座模型，再挂载 PEFT adapter：

```bash
uvicorn service.app:app --host 0.0.0.0 --port 8000 --workers 1
```

安装、环境变量和请求示例见 `service/README.md`。

## Mastra Agent

`mastra-agent/` 使用 OpenAI-compatible provider 调用本地 QLoRA 接口，并通过
Mastra tools 查询 mock 订单、物流、退款和创建工单。启动方式见
`mastra-agent/README.md`。

## 大文件

模型权重由 Git LFS 管理，已覆盖 `*.safetensors`、`*.bin`、`*.pt`、`*.pth` 和 `*.ckpt`。

## 安全说明

这是公开仓库。数据、样本和权重提交前应确认许可证及隐私要求。真实密码、令牌、SSH 私钥和其他密钥不得提交；请只填写 `.env.example` 的副本，并将真实值保存在环境变量或密钥管理服务中。
