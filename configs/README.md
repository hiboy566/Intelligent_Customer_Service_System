# Training configurations

Store reusable LLaMA-Factory YAML configuration files here.

For each run, record the exact configuration filename and Git commit in the corresponding `training_runs/` entry. Do not overwrite a configuration after it has been used; create a new version instead.

## Qwen3-VL-8B QLoRA smoke test

`qwen3_vl_8b_qlora_smoke.yaml` uses 4-bit NF4 QLoRA and the 50-record
`customer_service_smoke` dataset. Run it from the repository root:

```bash
llamafactory-cli train configs/qwen3_vl_8b_qlora_smoke.yaml
```

The adapter is written to `artifacts/qwen3-vl-8b/qlora/smoke`.

## Qwen3-VL-8B QLoRA training

`qwen3_vl_8b_qlora_train.yaml` trains on 500 records for three epochs and evaluates
against the independent 100-record validation set every 125 optimizer steps.

```bash
bash scripts/run_qwen3_vl_8b_qlora_train.sh
```

The best adapter is written to `artifacts/qwen3-vl-8b/qlora/train-v1`.

## Qwen3-VL-8B QLoRA evaluation

`qwen3_vl_8b_qlora_eval.yaml` loads the base model with the `train-v1` adapter and
generates answers for all 100 validation records using deterministic decoding.

```bash
bash scripts/run_qwen3_vl_8b_qlora_eval.sh
```

Predictions and text-generation metrics are written to
`artifacts/qwen3-vl-8b/qlora/eval-v1`.
