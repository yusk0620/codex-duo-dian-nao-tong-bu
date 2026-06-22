#!/bin/bash
# 🔄 stock-super-analysis — 多电脑同步脚本
# 用法: bash sync.sh
set -e
cd "$(dirname "$0")"
REPO="https://github.com/yusk0620/codex-duo-dian-nao-tong-bu.git"

if [ -d .git ]; then
    echo "🔄 同步最新版本..."
    git stash 2>/dev/null || true
    git pull origin main
    echo "✅ 已同步"
else
    echo "🔧 首次关联 GitHub..."
    git init
    git remote add origin "$REPO"
    git fetch origin main
    git reset --hard origin/main
    echo "✅ 已关联并同步"
fi

echo "📦 检查依赖..."
python3 -c "import baostock, pandas, numpy" 2>/dev/null || \
    python3 -m pip install --quiet baostock pandas numpy

echo "🎉 就绪! 用法: python3 run_analysis.py 000725"
