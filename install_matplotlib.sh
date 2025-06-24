#!/bin/bash
# LD2412 圖表功能安裝腳本

echo "🎨 安裝LD2412圖表功能所需套件..."

# 檢查Python版本
python3 --version

# 安裝matplotlib和numpy
echo "📊 安裝matplotlib..."
pip3 install matplotlib==3.8.2

echo "🔢 安裝numpy..."
pip3 install numpy==1.24.3

echo "✅ 安裝完成！"
echo ""
echo "新功能說明："
echo "📊 柱狀圖 - 清晰顯示各門能量分布"
echo "📈 趨勢圖 - 即時距離變化曲線"
echo "🎯 雷達圖 - 360度能量分布視圖"
echo "❄️ 圖表凍結 - 暫停更新以便分析"
echo "💾 圖表保存 - 高品質PNG/PDF輸出"
echo ""
echo "現在可以啟動GUI並享受更美觀的圖表顯示！"
echo "python3 ld2412_dark_gui.py" 