#!/usr/bin/env python3
import serial
import time

print("🔍 快速測試串列埠數據...")

try:
    # 連接串列埠
    ser = serial.Serial('/dev/cu.usbserial-0001', 115200, timeout=1)
    print(f"✅ 已連接到 {ser.name}")
    
    print("📡 正在接收數據 (5秒)...")
    start_time = time.time()
    raw_data = bytearray()
    
    while time.time() - start_time < 5:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            raw_data.extend(data)
            
            # 即時顯示收到的數據
            hex_str = ' '.join([f'{b:02X}' for b in data])
            print(f"收到: {hex_str}")
            
            # 嘗試解析為文字
            try:
                text = data.decode('utf-8', errors='ignore')
                if text.strip():
                    print(f"文字: {repr(text)}")
            except:
                pass
                
        time.sleep(0.01)
    
    print(f"\n📊 總共收到 {len(raw_data)} 字節")
    
    if len(raw_data) > 0:
        print("前32字節原始數據:")
        for i in range(min(32, len(raw_data))):
            print(f"{raw_data[i]:02X}", end=" ")
            if (i + 1) % 16 == 0:
                print()
        print()
        
        # 檢查是否包含LD2412幀頭
        if b'\xF4\xF3\xF2\xF1' in raw_data:
            print("✅ 發現LD2412數據幀頭!")
            pos = raw_data.find(b'\xF4\xF3\xF2\xF1')
            print(f"位置: {pos}")
        else:
            print("❌ 未發現LD2412數據幀頭")
            
        # 檢查是否為ESP8266調試輸出
        if b'\xe6\x95\xb8\xe6\x93\x9a' in raw_data:  # "數據" 的UTF-8編碼
            print("🔍 檢測到ESP8266中文調試輸出")
            
    else:
        print("❌ 未收到任何數據")
    
    ser.close()
    
except Exception as e:
    print(f"❌ 錯誤: {e}")

print("\n💡 分析結果:")
print("如果看到中文調試輸出，說明ESP8266在發送文字而非原始數據")
print("如果看到F4F3F2F1幀頭，說明是正確的LD2412原始數據") 