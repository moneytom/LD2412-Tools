#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import time
import sys
import os
from datetime import datetime
from collections import deque
import threading
import queue

class LD2412AnalyzerCLI:
    def __init__(self):
        # 串列埠設定
        self.port_name = "/dev/cu.usbserial-0001"
        self.baud_rate = 115200
        self.serial_port = None
        self.is_connected = False
        self.is_monitoring = False
        
        # 數據緩衝區
        self.raw_buffer = bytearray()
        self.data_queue = queue.Queue()
        
        # 數據歷史 (保留最近100筆)
        self.data_history = {
            'time': deque(maxlen=100),
            'moving_distance': deque(maxlen=100),
            'moving_energy': deque(maxlen=100),
            'still_distance': deque(maxlen=100),
            'still_energy': deque(maxlen=100),
            'detection_distance': deque(maxlen=100),
            'target_state': deque(maxlen=100),
            'light_value': deque(maxlen=100)
        }
        
        # 統計數據
        self.stats = {
            'total_frames': 0,
            'moving_detections': 0,
            'still_detections': 0,
            'no_target': 0,
            'max_distance': 0,
            'min_distance': 9999,
            'max_moving_energy': 0,
            'max_still_energy': 0,
            'start_time': time.time()
        }
        
        # 行為模式分析
        self.patterns = {
            'approach_count': 0,    # 接近次數
            'leave_count': 0,       # 離開次數
            'stable_count': 0,      # 穩定次數
            'last_distance': 0,     # 上次距離
            'distance_trend': []    # 距離趨勢 (最近10個)
        }
        
        # 警報設定
        self.alerts = {
            'close_range': 50,      # 近距離警報 (cm)
            'high_energy': 80,      # 高能量警報
            'rapid_approach': True  # 快速接近警報
        }
        
        # 顯示設定
        self.display_mode = 'full'  # full, stats, graph
        self.auto_scroll = True
        
    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def connect(self):
        try:
            self.serial_port = serial.Serial(self.port_name, self.baud_rate, timeout=1)
            self.is_connected = True
            print(f"✅ 成功連接到 {self.port_name}")
            return True
        except Exception as e:
            print(f"❌ 連接失敗: {e}")
            return False
    
    def disconnect(self):
        if self.serial_port:
            self.serial_port.close()
        self.is_connected = False
        self.is_monitoring = False
        print("已斷開連接")
    
    def send_start_command(self):
        if not self.is_connected:
            print("⚠️  請先連接串列埠")
            return
        
        try:
            # 發送開始數據輸出命令
            cmd = bytes.fromhex("FD FC FB FA 02 00 12 00 04 03 02 01")
            self.serial_port.write(cmd)
            self.serial_port.flush()
            print("📤 已發送啟動命令")
        except Exception as e:
            print(f"❌ 發送失敗: {e}")
    
    def data_reader_thread(self):
        """數據讀取線程"""
        while self.is_monitoring:
            if self.is_connected and self.serial_port:
                try:
                    if self.serial_port.in_waiting:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        self.raw_buffer.extend(data)
                        self.analyze_frames()
                except Exception as e:
                    self.data_queue.put(('error', str(e)))
            time.sleep(0.01)
    
    def analyze_frames(self):
        """分析數據幀"""
        buffer = bytes(self.raw_buffer)
        i = 0
        
        while i < len(buffer) - 7:
            # 查找數據幀頭 F4 F3 F2 F1
            if buffer[i:i+4] == b'\xF4\xF3\xF2\xF1':
                # 查找數據幀尾 F8 F7 F6 F5
                end_pos = -1
                for j in range(i + 8, min(i + 50, len(buffer) - 3)):
                    if buffer[j:j+4] == b'\xF8\xF7\xF6\xF5':
                        end_pos = j + 4
                        break
                
                if end_pos != -1:
                    frame = buffer[i:end_pos]
                    self.parse_data_frame(frame)
                    i = end_pos
                else:
                    i += 1
            else:
                i += 1
        
        # 清理已處理的數據
        if len(self.raw_buffer) > 1000:
            self.raw_buffer = self.raw_buffer[-500:]
    
    def parse_data_frame(self, frame):
        """解析數據幀"""
        if len(frame) < 23:
            return
        
        # 解析數據
        data_len = (frame[5] << 8) | frame[4]
        data_type = frame[6]
        head_ck = frame[7]
        
        target_state = frame[8]
        move_dist = (frame[10] << 8) | frame[9]
        move_energy = frame[11]
        still_dist = (frame[13] << 8) | frame[12]
        still_energy = frame[14]
        detect_dist = (frame[16] << 8) | frame[15]
        
        # 光感值（如果有）
        light_value = 0
        if len(frame) >= 21:
            light_value = frame[17]
        
        # 保存到歷史記錄
        current_time = time.time() - self.stats['start_time']
        self.data_history['time'].append(current_time)
        self.data_history['moving_distance'].append(move_dist)
        self.data_history['moving_energy'].append(move_energy)
        self.data_history['still_distance'].append(still_dist)
        self.data_history['still_energy'].append(still_energy)
        self.data_history['detection_distance'].append(detect_dist)
        self.data_history['target_state'].append(target_state)
        self.data_history['light_value'].append(light_value)
        
        # 更新統計
        self.update_statistics(target_state, move_dist, move_energy, still_dist, still_energy, detect_dist)
        
        # 行為分析
        self.analyze_behavior(detect_dist)
        
        # 檢查警報
        self.check_alerts(detect_dist, move_energy, still_energy)
        
        # 放入顯示隊列
        self.data_queue.put(('data', {
            'state': target_state,
            'move_dist': move_dist,
            'move_energy': move_energy,
            'still_dist': still_dist,
            'still_energy': still_energy,
            'detect_dist': detect_dist,
            'light': light_value
        }))
    
    def update_statistics(self, state, move_dist, move_energy, still_dist, still_energy, detect_dist):
        """更新統計數據"""
        self.stats['total_frames'] += 1
        
        if state & 0x01:  # 有目標
            if state & 0x02:  # 移動目標
                self.stats['moving_detections'] += 1
            if state & 0x04:  # 靜止目標
                self.stats['still_detections'] += 1
        else:
            self.stats['no_target'] += 1
        
        # 更新最大最小值
        if detect_dist > 0:
            self.stats['max_distance'] = max(self.stats['max_distance'], detect_dist)
            self.stats['min_distance'] = min(self.stats['min_distance'], detect_dist)
        
        self.stats['max_moving_energy'] = max(self.stats['max_moving_energy'], move_energy)
        self.stats['max_still_energy'] = max(self.stats['max_still_energy'], still_energy)
    
    def analyze_behavior(self, distance):
        """分析行為模式"""
        if distance > 0:
            # 更新距離趨勢
            self.patterns['distance_trend'].append(distance)
            if len(self.patterns['distance_trend']) > 10:
                self.patterns['distance_trend'].pop(0)
            
            # 分析趨勢
            if len(self.patterns['distance_trend']) >= 3:
                recent = self.patterns['distance_trend'][-3:]
                avg_change = (recent[-1] - recent[0]) / 2
                
                if avg_change < -30:  # 快速接近
                    self.patterns['approach_count'] += 1
                elif avg_change > 30:  # 快速離開
                    self.patterns['leave_count'] += 1
                else:
                    self.patterns['stable_count'] += 1
            
            self.patterns['last_distance'] = distance
    
    def check_alerts(self, distance, move_energy, still_energy):
        """檢查警報條件"""
        alerts = []
        
        # 近距離警報
        if 0 < distance < self.alerts['close_range']:
            alerts.append(f"⚠️  近距離檢測: {distance}cm")
        
        # 高能量警報
        if move_energy > self.alerts['high_energy']:
            alerts.append(f"⚡ 高移動能量: {move_energy}")
        if still_energy > self.alerts['high_energy']:
            alerts.append(f"⚡ 高靜止能量: {still_energy}")
        
        # 快速接近警報
        if len(self.patterns['distance_trend']) >= 3:
            if self.patterns['distance_trend'][-1] < self.patterns['distance_trend'][-3] - 50:
                alerts.append("🚨 檢測到快速接近!")
        
        # 顯示警報
        for alert in alerts:
            self.data_queue.put(('alert', alert))
    
    def display_full_analysis(self):
        """顯示完整分析界面"""
        self.clear_screen()
        
        print("=" * 80)
        print("                      LD2412 雷達數據即時分析系統")
        print("=" * 80)
        
        # 連接狀態
        status = "🟢 已連接" if self.is_connected else "🔴 未連接"
        monitor = "監控中..." if self.is_monitoring else "已停止"
        print(f"狀態: {status} | {monitor} | 運行時間: {int(time.time() - self.stats['start_time'])}秒")
        print("-" * 80)
        
        # 即時數據
        if len(self.data_history['target_state']) > 0:
            latest_state = self.data_history['target_state'][-1]
            state_text = self.get_state_text(latest_state)
            
            print(f"\n📊 即時數據:")
            print(f"  目標狀態: {state_text}")
            print(f"  移動距離: {self.data_history['moving_distance'][-1]:4d} cm  能量: {self.data_history['moving_energy'][-1]:3d}")
            print(f"  靜止距離: {self.data_history['still_distance'][-1]:4d} cm  能量: {self.data_history['still_energy'][-1]:3d}")
            print(f"  檢測距離: {self.data_history['detection_distance'][-1]:4d} cm  光感: {self.data_history['light_value'][-1]:3d}")
        
        # 統計分析
        print(f"\n📈 統計分析:")
        total = self.stats['total_frames']
        if total > 0:
            moving_rate = (self.stats['moving_detections'] / total) * 100
            still_rate = (self.stats['still_detections'] / total) * 100
            no_target_rate = (self.stats['no_target'] / total) * 100
            
            print(f"  總幀數: {total}")
            print(f"  移動檢測: {self.stats['moving_detections']} ({moving_rate:.1f}%)")
            print(f"  靜止檢測: {self.stats['still_detections']} ({still_rate:.1f}%)")
            print(f"  無目標: {self.stats['no_target']} ({no_target_rate:.1f}%)")
            print(f"  距離範圍: {self.stats['min_distance']} - {self.stats['max_distance']} cm")
            print(f"  最大能量: 移動={self.stats['max_moving_energy']} 靜止={self.stats['max_still_energy']}")
        
        # 行為模式
        print(f"\n🎯 行為模式:")
        print(f"  接近次數: {self.patterns['approach_count']}")
        print(f"  離開次數: {self.patterns['leave_count']}")
        print(f"  穩定次數: {self.patterns['stable_count']}")
        
        # 距離趨勢圖
        if len(self.data_history['detection_distance']) > 20:
            print(f"\n📉 距離趨勢 (最近20個數據點):")
            self.draw_mini_chart(list(self.data_history['detection_distance'])[-20:])
        
        # 能量分布圖
        if len(self.data_history['moving_energy']) > 20:
            print(f"\n⚡ 能量分布 (移動/靜止):")
            self.draw_dual_chart(
                list(self.data_history['moving_energy'])[-20:],
                list(self.data_history['still_energy'])[-20:]
            )
        
        print("\n" + "=" * 80)
        print("命令: [Q]退出 [C]清除數據 [S]發送啟動命令 [M]切換顯示模式")
    
    def get_state_text(self, state):
        """獲取狀態文字描述"""
        if state & 0x01:
            text = ""
            if state & 0x02:
                text += "🏃 移動目標 "
            if state & 0x04:
                text += "🧍 靜止目標"
            return text
        else:
            return "❌ 無目標"
    
    def draw_mini_chart(self, data, height=10):
        """繪製迷你圖表"""
        if not data:
            return
        
        max_val = max(data) if max(data) > 0 else 1
        min_val = min(data)
        
        # 正規化到0-height範圍
        normalized = []
        for val in data:
            norm = int((val - min_val) / (max_val - min_val) * height) if max_val != min_val else height // 2
            normalized.append(norm)
        
        # 繪製圖表
        for h in range(height, -1, -1):
            line = f"{max_val - (max_val - min_val) * (height - h) / height:4.0f} |"
            for n in normalized:
                if n >= h:
                    line += "█"
                else:
                    line += " "
            print(line)
        
        print("     " + "-" * len(data))
        print("     " + "".join([str(i % 10) for i in range(len(data))]))
    
    def draw_dual_chart(self, data1, data2, height=8):
        """繪製雙線圖表"""
        if not data1 or not data2:
            return
        
        all_data = data1 + data2
        max_val = max(all_data) if max(all_data) > 0 else 1
        
        # 正規化
        norm1 = [int(val / max_val * height) for val in data1]
        norm2 = [int(val / max_val * height) for val in data2]
        
        # 繪製
        for h in range(height, -1, -1):
            line = f"{int(max_val * h / height):3d} |"
            for i in range(len(norm1)):
                if norm1[i] >= h and norm2[i] >= h:
                    line += "▓"  # 重疊
                elif norm1[i] >= h:
                    line += "█"  # 移動能量
                elif norm2[i] >= h:
                    line += "░"  # 靜止能量
                else:
                    line += " "
            print(line)
        
        print("    " + "-" * len(data1))
        print("    █=移動 ░=靜止 ▓=重疊")
    
    def run(self):
        """主運行循環"""
        print("歡迎使用 LD2412 雷達數據分析系統!")
        print("正在連接...")
        
        if not self.connect():
            return
        
        print("正在發送啟動命令...")
        self.send_start_command()
        time.sleep(0.5)
        
        # 開始監控
        self.is_monitoring = True
        reader_thread = threading.Thread(target=self.data_reader_thread, daemon=True)
        reader_thread.start()
        
        # 主顯示循環
        last_update = time.time()
        
        try:
            while True:
                # 處理隊列中的消息
                while not self.data_queue.empty():
                    try:
                        msg_type, data = self.data_queue.get_nowait()
                        if msg_type == 'alert':
                            print(f"\n{data}")
                    except:
                        pass
                
                # 定期更新顯示 (每0.5秒)
                if time.time() - last_update > 0.5:
                    self.display_full_analysis()
                    last_update = time.time()
                
                # 檢查鍵盤輸入 (非阻塞)
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1).lower()
                    if key == 'q':
                        break
                    elif key == 'c':
                        self.clear_data()
                    elif key == 's':
                        self.send_start_command()
                    elif key == 'm':
                        self.toggle_display_mode()
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\n正在退出...")
        finally:
            self.is_monitoring = False
            self.disconnect()
            print("感謝使用!")
    
    def clear_data(self):
        """清除所有數據"""
        for key in self.data_history:
            self.data_history[key].clear()
        
        self.stats = {
            'total_frames': 0,
            'moving_detections': 0,
            'still_detections': 0,
            'no_target': 0,
            'max_distance': 0,
            'min_distance': 9999,
            'max_moving_energy': 0,
            'max_still_energy': 0,
            'start_time': time.time()
        }
        
        self.patterns = {
            'approach_count': 0,
            'leave_count': 0,
            'stable_count': 0,
            'last_distance': 0,
            'distance_trend': []
        }
        
        print("\n🗑️  已清除所有數據")
    
    def toggle_display_mode(self):
        """切換顯示模式"""
        modes = ['full', 'stats', 'graph']
        current_idx = modes.index(self.display_mode)
        self.display_mode = modes[(current_idx + 1) % len(modes)]
        print(f"\n切換到 {self.display_mode} 模式")

# 修正：使用更簡單的方式處理鍵盤輸入
import select

def main():
    analyzer = LD2412AnalyzerCLI()
    
    # 簡化版本 - 不使用select
    print("歡迎使用 LD2412 雷達數據分析系統!")
    print("正在連接...")
    
    if not analyzer.connect():
        return
    
    print("正在發送啟動命令...")
    analyzer.send_start_command()
    time.sleep(0.5)
    
    # 開始監控
    analyzer.is_monitoring = True
    reader_thread = threading.Thread(target=analyzer.data_reader_thread, daemon=True)
    reader_thread.start()
    
    # 主顯示循環
    last_update = time.time()
    
    try:
        while True:
            # 處理隊列中的消息
            while not analyzer.data_queue.empty():
                try:
                    msg_type, data = analyzer.data_queue.get_nowait()
                    if msg_type == 'alert':
                        print(f"\n{data}")
                except:
                    pass
            
            # 定期更新顯示 (每0.5秒)
            if time.time() - last_update > 0.5:
                analyzer.display_full_analysis()
                last_update = time.time()
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n正在退出...")
    finally:
        analyzer.is_monitoring = False
        analyzer.disconnect()
        print("感謝使用!")

if __name__ == "__main__":
    main() 