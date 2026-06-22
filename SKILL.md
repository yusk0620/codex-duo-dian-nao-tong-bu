---
name: stock-super-analysis
description: |
  🔬 一键股票五维分析流水线。当你提到任何A股/港股/美股代码时自动触发。
  
  串行调用5个Skill的框架方法：
  1. UZI-Skill — 22维深度分析（趋势/量能/动能/波动/支撑压力）
  2. TradingAgents — 多智能体信号（多空/估值/动量综合打分）
  3. Serenity Skill — 产业链/供应链卡点分析
  4. Buffett Skills — 价值投资清单（PE/PB/ROE/护城河/安全边际）
  5. QuantDinger — 量化信号矩阵（MA交叉/量价/波动率/RSI/Bollinger）
  
  最后调用 DeepSeek API 生成总结 + 建议买入参考价。

trigger: Always run this skill when the user asks about any stock (e.g. "分析600011", "帮我看看159971", "AAPL怎么样", "看一下茅台")

pipeline:
  - Parse stock code from user input
  - Run run_analysis.py with the stock code(s)
  - Display the 5-dimension analysis report
  - Call DeepSeek for final summary and suggested entry price

execution:
  python3 "$SKILL_DIR/run_analysis.py" "<stock_codes>"

setup:
  - pip3 install baostock pandas numpy
  - echo "sk-your-key" > ~/.deepseek_key
