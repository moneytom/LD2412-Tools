#!/usr/bin/env python3
import serial
import time

def test_raw_data():
    print("🧪 測試原始LD2412數據接收...")
    
    try:
        # 連接串列埠
        ser = serial.Serial('/dev/cu.usbserial-0001', 115200, timeout=1)
        print(f"✅ 已連接到 {ser.name}")
        
        # 發送啟動數據輸出命令
        start_cmd = bytes.fromhex("FD FC FB FA 02 00 12 00 04 03 02 01")
        ser.write(start_cmd)
        ser.flush()
        print("📤 已發送啟動數據輸出命令")
        
        print("📡 等待LD2412數據 (10秒)...")
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < 10:
            if ser.in_waiting:
                data = ser.read(ser.in_waiting)
                
                # 檢查是否為原始二進制數據
                is_binary = True
                text_chars = 0
                
                for byte in data:
                    # 檢查是否為可列印ASCII字符 (表示是文字)
                    if 32 <= byte <= 126 or byte in [9, 10, 13]:  # 可列印字符或空白字符
                        text_chars += 1
                
                # 如果超過50%是文字字符，可能是調試輸出
                if len(data) > 0 and text_chars / len(data) > 0.5:
                    print(f"⚠️ 收到疑似文字數據: {text_chars}/{len(data)} 字符是文字")
                    try:
                        text = data.decode('utf-8', errors='ignore')
                        print(f"文字內容: {repr(text[:100])}")
                    except:
                        pass
                else:
                    # 原始二進制數據
                    hex_str = ' '.join([f'{b:02X}' for b in data])
                    print(f"📡 原始數據: {hex_str}")
                    
                    # 查找LD2412數據幀
                    for i in range(len(data) - 3):
                        if data[i:i+4] == b'\xF4\xF3\xF2\xF1':
                            frame_count += 1
                            print(f"✅ 發現數據幀 #{frame_count} 於位置 {i}")
                            
                            # 嘗試找到幀尾
                            for j in range(i+8, min(i+50, len(data)-3)):
                                if data[j:j+4] == b'\xF8\xF7\xF6\xF5':
                                    frame_len = j + 4 - i
                                    frame = data[i:j+4]
                                    print(f"  完整幀長度: {frame_len} 字節")
                                    
                                    # 簡單解析
                                    if frame_len >= 21:
                                        target_state = frame[8]
                                        move_dist = (frame[10] << 8) | frame[9]
                                        still_dist = (frame[13] << 8) | frame[12]
                                        detect_dist = (frame[16] << 8) | frame[15]
                                        
                                        print(f"  目標狀態: 0x{target_state:02X}")
                                        print(f"  移動距離: {move_dist} cm")
                                        print(f"  靜止距離: {still_dist} cm") 
                                        print(f"  檢測距離: {detect_dist} cm")
                                    break
                            break
                            
            time.sleep(0.01)
        
        print(f"\n📊 總共發現 {frame_count} 個完整數據幀")
        
        if frame_count > 0:
            print("🎉 成功！收到正確的LD2412原始數據")
        else:
            print("❌ 未收到正確的LD2412數據幀")
            print("💡 可能需要:")
            print("  1. 重新上傳ESP8266透明轉發程序")
            print("  2. 檢查LD2412接線")
            print("  3. 確認LD2412供電正常")
        
        ser.close()
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == "__main__":
    test_raw_data() 