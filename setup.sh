#!/bin/bash
# 🔬 stock-super-analysis — 首次安装脚本
# 用法: bash setup.sh
set -e

echo "🔬 股票五维分析 — 安装依赖..."
python3 -m pip install --quiet baostock pandas numpy

if [ ! -f ~/.deepseek_key ]; then
    echo ""
    echo "🔑 请输入 DeepSeek API Key (platform.deepseek.com → API Keys):"
    read -r ds_key
    echo "$ds_key" > ~/.deepseek_key
    chmod 600 ~/.deepseek_key
    echo "✅ 已保存"
else
    echo "✅ DeepSeek Key 已存在"
fi

echo "🎉 完成! 用法: python3 run_analysis.py 000725"
