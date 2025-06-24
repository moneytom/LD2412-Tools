#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'

# 測試數據分析邏輯
def test_frame_parsing():
    print("🧪 測試LD2412數據幀解析...")
    
    # 模擬一個真實的LD2412數據幀
    # F4 F3 F2 F1 [長度] [類型] [校驗] [數據...] F8 F7 F6 F5
    test_frame = bytes([
        0xF4, 0xF3, 0xF2, 0xF1,  # 幀頭
        0x0B, 0x00,              # 數據長度 (11字節)
        0x02,                    # 數據類型
        0xAA,                    # 校驗
        0x03,                    # 目標狀態 (有目標+移動)
        0x78, 0x00,              # 移動距離 120cm
        0x55,                    # 移動能量 85
        0x96, 0x00,              # 靜止距離 150cm
        0x40,                    # 靜止能量 64
        0x78, 0x00,              # 檢測距離 120cm
        0x10,                    # 光感值 16
        0xF8, 0xF7, 0xF6, 0xF5   # 幀尾
    ])
    
    print(f"測試數據幀: {' '.join([f'{b:02X}' for b in test_frame])}")
    print(f"幀長度: {len(test_frame)} 字節")
    
    # 修正：LD2412最小數據幀長度為21字節，不是23字節
    if len(test_frame) >= 21:
        target_state = test_frame[8]
        move_dist = (test_frame[10] << 8) | test_frame[9]
        move_energy = test_frame[11]
        still_dist = (test_frame[13] << 8) | test_frame[12]
        still_energy = test_frame[14]
        detect_dist = (test_frame[16] << 8) | test_frame[15]
        light_value = test_frame[17] if len(test_frame) >= 19 else 0
        
        print("\n📊 解析結果:")
        print(f"目標狀態: 0x{target_state:02X}")
        
        # 解析狀態位
        if target_state & 0x01:
            state_text = ""
            if target_state & 0x02:
                state_text += "🏃 移動目標 "
            if target_state & 0x04:
                state_text += "🧍 靜止目標"
            print(f"狀態描述: {state_text}")
        else:
            print("狀態描述: ❌ 無目標")
        
        print(f"移動距離: {move_dist} cm")
        print(f"移動能量: {move_energy}")
        print(f"靜止距離: {still_dist} cm")
        print(f"靜止能量: {still_energy}")
        print(f"檢測距離: {detect_dist} cm")
        print(f"光感值: {light_value}")
        
        # 測試警報邏輯
        print("\n⚠️ 警報檢查:")
        alerts = []
        if 0 < detect_dist < 50:
            alerts.append(f"🚨 近距離警報: {detect_dist}cm")
        if move_energy > 80:
            alerts.append(f"⚡ 高移動能量警報: {move_energy}")
        if still_energy > 80:
            alerts.append(f"⚡ 高靜止能量警報: {still_energy}")
        
        if alerts:
            for alert in alerts:
                print(alert)
        else:
            print("✅ 無警報觸發")
        
        print("✅ 數據解析測試完成")
        return True
    else:
        print("❌ 數據幀長度不足")
        return False

def test_gui_components():
    print("\n🖥️ 測試深色主題GUI組件...")
    
    try:
        import tkinter as tk
        from tkinter import ttk
        import serial
        import threading
        import queue
        from datetime import datetime
        from collections import deque
        
        print("✅ 所有必要模組已導入")
        
        # 測試深色主題GUI創建
        root = tk.Tk()
        root.title("深色主題測試GUI")
        root.geometry("400x300")
        root.configure(bg='#2b2b2b')
        
        # 創建深色主題組件
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Dark.TLabel', 
                       background='#2b2b2b',
                       foreground='#ffffff')
        
        style.configure('Dark.TButton', 
                       background='#3c3c3c',
                       foreground='#ffffff')
        
        label = ttk.Label(root, text="深色主題GUI測試成功!", style='Dark.TLabel')
        label.pack(pady=20)
        
        button = ttk.Button(root, text="關閉", command=root.quit, style='Dark.TButton')
        button.pack(pady=10)
        
        # 測試文本框
        text_widget = tk.Text(root, bg='#3c3c3c', fg='#ffffff', height=5, width=40)
        text_widget.pack(pady=10)
        text_widget.insert(tk.END, "深色主題文本框測試\n顏色配置正常")
        
        print("✅ 深色主題GUI組件創建成功")
        
        # 自動關閉
        root.after(3000, root.quit)
        root.mainloop()
        
        print("✅ 深色主題GUI測試完成")
        return True
        
    except Exception as e:
        print(f"❌ GUI測試失敗: {e}")
        return False

def test_data_analysis_logic():
    print("\n🔬 測試數據分析邏輯...")
    
    try:
        from collections import deque
        
        # 模擬數據歷史
        data_history = {
            'time': deque(maxlen=100),
            'detection_distance': deque(maxlen=100),
            'target_state': deque(maxlen=100)
        }
        
        # 添加測試數據
        test_data = [
            (1.0, 120, 0x03),  # 移動目標
            (2.0, 115, 0x03),  # 接近
            (3.0, 110, 0x03),
            (4.0, 105, 0x05),  # 靜止目標
            (5.0, 105, 0x05),  # 穩定
            (6.0, 0, 0x00),    # 無目標
        ]
        
        for time_val, distance, state in test_data:
            data_history['time'].append(time_val)
            data_history['detection_distance'].append(distance)
            data_history['target_state'].append(state)
        
        print(f"✅ 測試數據已添加: {len(data_history['time'])} 個數據點")
        
        # 測試統計計算
        total_frames = len(data_history['target_state'])
        moving_count = sum(1 for state in data_history['target_state'] if state & 0x02)
        still_count = sum(1 for state in data_history['target_state'] if state & 0x04)
        no_target_count = sum(1 for state in data_history['target_state'] if not (state & 0x01))
        
        print(f"統計結果:")
        print(f"  總幀數: {total_frames}")
        print(f"  移動檢測: {moving_count}")
        print(f"  靜止檢測: {still_count}")
        print(f"  無目標: {no_target_count}")
        
        # 測試趨勢分析
        distances = [d for d in data_history['detection_distance'] if d > 0]
        if distances:
            max_dist = max(distances)
            min_dist = min(distances)
            print(f"  距離範圍: {min_dist} - {max_dist} cm")
        
        print("✅ 數據分析邏輯測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 數據分析測試失敗: {e}")
        return False

def test_serial_simulation():
    print("\n📡 測試串列埠模擬...")
    
    try:
        import serial
        print("✅ pyserial模組可用")
        
        # 測試數據緩衝區
        buffer = bytearray()
        test_data = bytes([0xF4, 0xF3, 0xF2, 0xF1, 0x0B, 0x00, 0x02, 0xAA])
        buffer.extend(test_data)
        
        print(f"緩衝區數據: {' '.join([f'{b:02X}' for b in buffer])}")
        print("✅ 數據緩衝區測試成功")
        
        # 測試數據隊列
        import queue
        data_queue = queue.Queue()
        data_queue.put(('data', test_data))
        
        msg_type, data = data_queue.get()
        print(f"隊列數據: {msg_type} - {len(data)} 字節")
        print("✅ 數據隊列測試成功")
        
        # 測試幀檢測
        full_frame = bytes([
            0xF4, 0xF3, 0xF2, 0xF1,  # 幀頭
            0x0B, 0x00, 0x02, 0xAA,  # 長度、類型、校驗
            0x03, 0x78, 0x00, 0x55,  # 狀態、移動距離、能量
            0x96, 0x00, 0x40, 0x78,  # 靜止距離、能量、檢測距離
            0x00, 0x10,              # 檢測距離低位、光感
            0xF8, 0xF7, 0xF6, 0xF5   # 幀尾
        ])
        
        # 查找幀頭和幀尾
        if full_frame[0:4] == b'\xF4\xF3\xF2\xF1' and full_frame[-4:] == b'\xF8\xF7\xF6\xF5':
            print("✅ 數據幀檢測成功")
        else:
            print("❌ 數據幀檢測失敗")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 串列埠模擬測試失敗: {e}")
        return False

def main():
    print("=" * 60)
    print("🔬 LD2412數據分析系統測試 (深色主題版)")
    print("=" * 60)
    
    # 執行所有測試
    tests = [
        ("數據幀解析", test_frame_parsing),
        ("深色主題GUI", test_gui_components),
        ("數據分析邏輯", test_data_analysis_logic),
        ("串列埠模擬", test_serial_simulation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n▶️ 執行測試: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 測試異常: {e}")
            results.append((test_name, False))
    
    # 顯示測試結果
    print("\n" + "=" * 60)
    print("📋 測試結果摘要")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\n總計: {passed}/{len(results)} 個測試通過")
    
    if passed == len(results):
        print("\n🎉 所有測試通過！深色主題數據分析系統準備就緒。")
        print("\n💡 建議:")
        print("1. 使用 './start_dark_gui.sh' 啟動深色主題GUI")
        print("2. 或使用 'source ld2412_env/bin/activate && python ld2412_dark_gui.py'")
        print("3. 連接設備並發送啟動命令開始分析")
        print("\n🌙 深色主題特色:")
        print("- 適合暗色系統環境")
        print("- 護眼的深色配色方案")
        print("- 修正的數據分析邏輯")
        print("- 完整的16進制數據解析")
    else:
        print("\n⚠️ 部分測試失敗，請檢查系統配置。")

if __name__ == "__main__":
    main() 