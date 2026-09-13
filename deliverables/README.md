# 交付物

本目录存放 Stage 6 最终交付物：

- `DELIVERY_GUIDE.md`：最终交付指南（资产构成、Agent 关系、上传包、history_level、来源类型、上传顺序、维护原则、已知边界）。
- `rag/`：RAG 发布版（239 项资产 + RAG_MANIFEST.csv + PROJECT_INDEX.csv + build_report.json），由 `scripts/build_rag_package.py` 从 `knowledge/` 生成；治理原版仍在 `knowledge/`，不以上传版覆盖。
- `packages/`：四个根目录平铺的上传 ZIP（每包 ≤100 文件），由 `scripts/build_upload_packages.py` 生成：
  - `PACKAGE-01_CORE.zip`（100 份核心知识）
  - `PACKAGE-02_PROJECT_MEMORY.zip`（99 份项目案例）
  - `PACKAGE-03_BUSINESS_DATA.zip`（12 份 XLSX + PROJECT_INDEX.csv）
  - `PACKAGE-04_TEMPLATES.zip`（28 份模板）

各 Stage 的中间报告归档于 `archive/`，不再作为活动交付物。
