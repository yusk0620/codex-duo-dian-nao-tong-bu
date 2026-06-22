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

## 安装 (Codex Skill)

```bash
# 首次: 装依赖 + 配置 DeepSeek Key
bash setup.sh

# 分析股票
python3 run_analysis.py 000725
python3 run_analysis.py 600011 603993
```

## 双源实时行情

eastmoney (主) → Sina (备) → baostock 日线降级。
