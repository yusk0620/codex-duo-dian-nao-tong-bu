# 🔬 stock-super-analysis

一键 A 股五维分析 + 实时价格 + DeepSeek 总结建议。

## 五维引擎

| 引擎 | 评分 |
|------|------|
| UZI · 趋势追踪 | 0-7 |
| TradingAgents · 多空信号 | 标签 |
| Serenity · 供应链卡点 | 定性 |
| Buffett · 价值清单 | 0-8 |
| QuantDinger · 量化信号 | 0-100 |

## 安装

```bash
bash setup.sh     # 首次: 装依赖 + 配 DeepSeek Key
python3 run_analysis.py 000725
```

## 多电脑同步

```bash
bash sync.sh      # 从 GitHub 拉取最新版本
```

每台电脑改完代码 `git push` 后，其他电脑跑 `bash sync.sh` 即可同步。
