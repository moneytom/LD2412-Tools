#!/bin/bash

# ESP8266 UART測試程序上傳腳本
# 正確處理多個cpp文件的編譯衝突問題

echo "🔧 ESP8266 SoftwareSerial UART配置測試"
echo "測試目標: RX=GPIO15, TX=GPIO2 與 LD2412 通信"
echo "=========================================="

# 檢查platformio是否已安裝
if ! command -v pio &> /dev/null; then
    echo "❌ PlatformIO未安裝，正在安裝..."
    pip3 install platformio
fi

# 創建備份目錄
echo "📦 準備備份目錄..."
mkdir -p backup_src

# 備份所有非主要的cpp文件，避免編譯衝突
echo "🔄 備份其他cpp文件以避免編譯衝突..."

# 備份當前main.cpp
if [ -f "src/main.cpp" ]; then
    cp src/main.cpp backup_src/main.cpp.original
    echo "✅ 已備份原main.cpp"
fi

# 移動其他cpp文件到備份目錄（避免多個setup/loop函數衝突）
for file in src/*.cpp; do
    filename=$(basename "$file")
    if [ "$filename" != "main.cpp" ]; then
        echo "  移動 $filename 到備份目錄"
        mv "$file" "backup_src/"
    fi
done

# 複製UART測試程序為新的main.cpp
echo "🔄 部署UART測試程序..."
cp backup_src/uart_test.cpp src/main.cpp

# 編譯並上傳
echo "🔨 編譯程序..."
pio run -e esp12e

if [ $? -eq 0 ]; then
    echo "✅ 編譯成功"
    echo "📤 上傳到ESP8266..."
    pio run -e esp12e -t upload
    
    if [ $? -eq 0 ]; then
        echo "✅ 上傳成功"
        echo ""
        echo "🔍 UART測試程序功能:"
        echo "• 測試SoftwareSerial(15,2)配置"
        echo "• 測試256000和115200波特率"
        echo "• 驗證LD2412通信協議"
        echo "• 顯示詳細統計報告"
        echo ""
        echo "📊 監控輸出:"
        echo "pio device monitor -b 115200"
        echo ""
        echo "🔄 測試完成後恢復原程序:"
        echo "./restore_original.sh"
    else
        echo "❌ 上傳失敗，請檢查ESP8266連接"
        # 恢復文件
        restore_files
    fi
else
    echo "❌ 編譯失敗，請檢查程式碼"
    # 恢復文件
    restore_files
fi

# 創建恢復腳本
cat > restore_original.sh << 'EOF'
#!/bin/bash
echo "🔄 恢復原始程序..."

# 恢復原始main.cpp
if [ -f "backup_src/main.cpp.original" ]; then
    cp backup_src/main.cpp.original src/main.cpp
    echo "✅ 已恢復原始main.cpp"
fi

# 恢復其他cpp文件
for file in backup_src/*.cpp; do
    filename=$(basename "$file")
    if [ "$filename" != "main.cpp.original" ]; then
        cp "$file" "src/"
        echo "  恢復 $filename"
    fi
done

echo "📤 重新編譯上傳..."
pio run -e esp12e -t upload

if [ $? -eq 0 ]; then
    echo "✅ 原始程序恢復成功"
else
    echo "❌ 恢復失敗，請手動檢查"
fi
EOF

chmod +x restore_original.sh
echo "✅ 已創建恢復腳本: restore_original.sh"

function restore_files() {
    echo "🔄 恢復文件..."
    # 恢復原始main.cpp
    if [ -f "backup_src/main.cpp.original" ]; then
        cp backup_src/main.cpp.original src/main.cpp
    fi
    
    # 恢復其他cpp文件
    for file in backup_src/*.cpp; do
        filename=$(basename "$file")
        if [ "$filename" != "main.cpp.original" ]; then
            cp "$file" "src/"
        fi
    done
} 