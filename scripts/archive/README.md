# 脚本归档

`generate_stage1.py` 为 Stage 1/1.1 一次性生成器，已归档，不再作为活动生成入口；其中记录的旧路径（如 `source_registry/`）不再有效。

`generate_stage3.py` 为 Stage 3 一次性批量生成器，Stage 3 已完成后归档。该脚本直接重写 `knowledge/core/` 下 100 份正式正文和 `manifests/CLAIM_PROVENANCE.csv`，无覆盖保护，仅保留历史复现用途，不得作为活动入口再次运行。

活动脚本只保留 `scripts/` 下的校验器；统一校验入口为 `scripts/validate_all.py`。归档脚本不被 validator 读取，不参与正式校验。
