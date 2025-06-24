#!/bin/bash

# 清理src目錄，避免多個cpp文件編譯衝突

echo "🧹 清理src目錄以避免編譯衝突"
echo "================================"

# 創建備份目錄
mkdir -p backup_src

# 顯示當前src目錄內容
echo "📁 當前src目錄內容:"
ls -la src/*.cpp

echo ""
echo "🔄 處理方案選擇:"
echo "1. 只保留main.cpp，其他文件移動到backup_src/"
echo "2. 重命名其他文件為.bak後綴"
echo "3. 取消操作"

read -p "請選擇 (1/2/3): " choice

case $choice in
    1)
        echo "📦 移動其他cpp文件到backup_src/..."
        for file in src/*.cpp; do
            filename=$(basename "$file")
            if [ "$filename" != "main.cpp" ]; then
                echo "  移動 $filename"
                mv "$file" "backup_src/"
            fi
        done
        echo "✅ 完成！現在只有main.cpp會被編譯"
        ;;
    2)
        echo "🏷️ 重命名其他cpp文件..."
        for file in src/*.cpp; do
            filename=$(basename "$file")
            if [ "$filename" != "main.cpp" ]; then
                echo "  重命名 $filename -> $filename.bak"
                mv "$file" "$file.bak"
            fi
        done
        echo "✅ 完成！.bak文件不會被編譯"
        ;;
    3)
        echo "❌ 操作已取消"
        exit 0
        ;;
    *)
        echo "❌ 無效選擇"
        exit 1
        ;;
esac

echo ""
echo "📁 處理後的src目錄:"
ls -la src/

echo ""
echo "💡 恢復文件方法:"
if [ "$choice" = "1" ]; then
    echo "cp backup_src/*.cpp src/"
else
    echo "for f in src/*.bak; do mv \"\$f\" \"\${f%.bak}\"; done"
fi 