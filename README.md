# quant-lab

个人 A 股量化工具：收盘后自动拉数据、算因子、出信号，人工下单。不接实盘。

## 目录

| 路径 | 内容 |
|---|---|
| `server/` | Python 服务，包名 `app`，无 `src/` 层：`domain` `data` `quant` `workflow` `api` 等，见 D001 第 10 章 |
| `server/config/` | 走 git 的运行时参数（同步顺序、门禁阈值） |
| `desktop/` | Go：Wails 桌面壳（M4） |
| `web/` | TypeScript：React 前端（M4） |
| `scripts/` | 跨语言脚本：release、backup |
| `deploy/` | systemd 模板、Ubuntu 安装说明 |
| `docs/` | 规范、SPEC、runbook |
| `data/` | 默认数据根，`QUANT_LAB_DATA_ROOT` 可改；只提交 `.keep` |

## 开发

```bash
cd server
uv sync
uv run python -m app --help
uv run scripts/check.sh     # ruff + pyright + pytest，CI 跑同一个脚本
```

架构设计见 `.context/decisions/D001-architecture.md`（本地文件，不进 git）。
