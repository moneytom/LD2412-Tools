#!/bin/bash

# LD2412 深色主題GUI啟動腳本
# 使用Python 3.13虛擬環境

echo "🌙 啟動LD2412雷達控制GUI (深色主題)..."
echo "Python 3.13 虛擬環境"
echo "================================"

# 檢查虛擬環境是否存在
if [ ! -d "ld2412_env" ]; then
    echo "❌ 虛擬環境不存在，正在創建..."
    python3.13 -m venv ld2412_env
    echo "✅ 虛擬環境創建完成"
fi

# 啟動虛擬環境
source ld2412_env/bin/activate

# 檢查依賴
echo "🔍 檢查依賴..."
python -c "import serial" 2>/dev/null || {
    echo "📦 安裝pyserial..."
    pip install pyserial
}

python -c "import tkinter" 2>/dev/null || {
    echo "❌ tkinter不可用，請檢查Python安裝"
    exit 1
}

echo "✅ 所有依賴已準備就緒"
echo "🎯 啟動深色主題GUI界面..."
echo ""
echo "深色主題GUI功能說明："
echo "- 🌙 深色主題界面，適合暗色系統"
echo "- 🔌 連接LD2412設備"
echo "- 📤 發送控制命令"
echo "- 📊 即時數據分析"
echo "- 🔍 16進制數據解析"
echo "- ⚠️ 智能警報系統"
echo "- 📉 ASCII圖表顯示"
echo ""

# 設置環境變數並啟動GUI
export TK_SILENCE_DEPRECATION=1
python ld2412_dark_gui.py

echo ""
echo "👋 深色主題GUI已關閉，感謝使用！" 