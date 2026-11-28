# server/config

走 git 的运行时参数。服务启动时读取，运行时不回写。

- `pipeline.toml`：同步顺序、各数据集开关、时间表
- `quality.toml`：门禁阈值（行数波动、缺失率、价格跳变），历史数据回填后按实际分布定

本机密钥（Tushare token 等）不在这里，放数据根下的 `config.toml`（默认 `data/config.toml`）或环境变量，见架构文档 3.3。
