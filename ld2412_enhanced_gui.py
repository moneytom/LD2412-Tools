#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial
import threading
import time
import queue
from datetime import datetime
from collections import deque
import os

# 消除macOS上的tkinter警告
os.environ['TK_SILENCE_DEPRECATION'] = '1'

class EnhancedLD2412GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LD2412 雷達數據分析與控制系統 v2.0")
        self.root.geometry("1400x900")
        
        # 串列埠設定
        self.port_name = "/dev/cu.usbserial-0001"
        self.baud_rate = 115200
        self.serial_port = None
        self.is_connected = False
        self.is_monitoring = False
        
        # 數據處理
        self.data_queue = queue.Queue()
        self.raw_buffer = bytearray()
        
        # 數據歷史 (增加容量)
        self.data_history = {
            'time': deque(maxlen=200),
            'moving_distance': deque(maxlen=200),
            'moving_energy': deque(maxlen=200),
            'still_distance': deque(maxlen=200),
            'still_energy': deque(maxlen=200),
            'detection_distance': deque(maxlen=200),
            'target_state': deque(maxlen=200),
            'light_value': deque(maxlen=200)
        }
        
        # 統計數據
        self.stats = {
            'total_frames': 0,
            'moving_detections': 0,
            'still_detections': 0,
            'no_target': 0,
            'start_time': time.time(),
            'max_distance': 0,
            'min_distance': 9999,
            'avg_moving_energy': 0,
            'avg_still_energy': 0,
            'last_update': time.time()
        }
        
        # 行為分析
        self.behavior = {
            'approach_count': 0,
            'leave_count': 0,
            'stable_count': 0,
            'noise_count': 0,
            'last_distances': deque(maxlen=10),
            'state_changes': deque(maxlen=20)
        }
        
        # 當前數據
        self.current_data = None
        
        self.create_widgets()
        self.start_data_thread()
        self.update_display()
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. 控制區域
        self.create_control_panel(main_frame)
        
        # 2. 數據顯示區域
        self.create_data_area(main_frame)
        
        # 3. 日誌區域
        self.create_log_area(main_frame)
        
        # 初始化
        self.log("🚀 系統啟動完成，請連接設備開始使用")
        self.update_realtime_display()
        
    def create_control_panel(self, parent):
        control_frame = ttk.LabelFrame(parent, text="🎛️ 控制面板", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 連接控制
        conn_frame = ttk.Frame(control_frame)
        conn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(conn_frame, text="串列埠:").pack(side=tk.LEFT, padx=5)
        self.port_var = tk.StringVar(value=self.port_name)
        ttk.Entry(conn_frame, textvariable=self.port_var, width=25).pack(side=tk.LEFT, padx=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="🔌 連接", command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.monitor_btn = ttk.Button(conn_frame, text="▶️ 開始監控", command=self.toggle_monitoring)
        self.monitor_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(conn_frame, text="🔴 未連接", font=("Arial", 12, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # 即時狀態顯示
        status_frame = ttk.Frame(conn_frame)
        status_frame.pack(side=tk.RIGHT, padx=20)
        
        self.frame_count_label = ttk.Label(status_frame, text="數據幀: 0", font=("Arial", 10))
        self.frame_count_label.pack(side=tk.LEFT, padx=10)
        
        self.fps_label = ttk.Label(status_frame, text="幀率: 0.0/s", font=("Arial", 10))
        self.fps_label.pack(side=tk.LEFT, padx=10)
        
        # 命令按鈕
        cmd_frame = ttk.LabelFrame(control_frame, text="📤 命令控制", padding="5")
        cmd_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 常用命令按鈕
        commands = [
            ("🚀 啟動數據輸出", "FD FC FB FA 02 00 12 00 04 03 02 01"),
            ("📋 查詢版本", "FD FC FB FA 02 00 A0 00 04 03 02 01"),
            ("⚙️ 進入配置", "FD FC FB FA 04 00 FF 00 01 00 04 03 02 01"),
            ("🚪 退出配置", "FD FC FB FA 02 00 FE 00 04 03 02 01"),
            ("🔄 重啟", "FD FC FB FA 02 00 A3 00 04 03 02 01"),
            ("⏹️ 停止輸出", "FD FC FB FA 02 00 13 00 04 03 02 01"),
            ("🏭 恢復出廠", "FD FC FB FA 02 00 A2 00 04 03 02 01"),
            ("🗑️ 清除數據", None)
        ]
        
        for i, (name, cmd) in enumerate(commands):
            if cmd:
                btn = ttk.Button(cmd_frame, text=name, 
                               command=lambda c=cmd: self.send_command(c))
            else:
                btn = ttk.Button(cmd_frame, text=name, command=self.clear_data)
            btn.grid(row=i//4, column=i%4, padx=3, pady=2, sticky=tk.W)
        
        # 自定義命令
        custom_frame = ttk.Frame(cmd_frame)
        custom_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(custom_frame, text="自定義命令:").pack(side=tk.LEFT, padx=5)
        self.custom_cmd_var = tk.StringVar()
        ttk.Entry(custom_frame, textvariable=self.custom_cmd_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(custom_frame, text="📤 發送", command=self.send_custom_command).pack(side=tk.LEFT, padx=5)
        
    def create_data_area(self, parent):
        data_frame = ttk.Frame(parent)
        data_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左側面板 - 分析結果
        left_frame = ttk.Frame(data_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 即時數據
        realtime_frame = ttk.LabelFrame(left_frame, text="📊 即時數據分析", padding="10")
        realtime_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.realtime_text = tk.Text(realtime_frame, height=10, font=("Courier", 11), bg="#f8f9fa")
        self.realtime_text.pack(fill=tk.X)
        
        # 統計分析
        stats_frame = ttk.LabelFrame(left_frame, text="📈 統計分析", padding="10")
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_text = tk.Text(stats_frame, height=8, font=("Courier", 10), bg="#f0f8ff")
        self.stats_text.pack(fill=tk.X)
        
        # 行為分析
        behavior_frame = ttk.LabelFrame(left_frame, text="🎯 行為模式分析", padding="10")
        behavior_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.behavior_text = tk.Text(behavior_frame, height=6, font=("Courier", 10), bg="#f0fff0")
        self.behavior_text.pack(fill=tk.X)
        
        # 距離趨勢圖
        chart_frame = ttk.LabelFrame(left_frame, text="📉 距離趨勢圖", padding="10")
        chart_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chart_text = tk.Text(chart_frame, font=("Courier", 8), bg="#fffef0")
        self.chart_text.pack(fill=tk.BOTH, expand=True)
        
        # 右側面板 - 原始數據
        right_frame = ttk.Frame(data_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 原始數據
        raw_frame = ttk.LabelFrame(right_frame, text="🔢 原始16進制數據", padding="5")
        raw_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.raw_text = scrolledtext.ScrolledText(raw_frame, font=("Courier", 9))
        self.raw_text.pack(fill=tk.BOTH, expand=True)
        
        # 解析結果
        parsed_frame = ttk.LabelFrame(right_frame, text="🔍 詳細解析結果", padding="5")
        parsed_frame.pack(fill=tk.BOTH, expand=True)
        
        self.parsed_text = scrolledtext.ScrolledText(parsed_frame, font=("Courier", 9))
        self.parsed_text.pack(fill=tk.BOTH, expand=True)
        
    def create_log_area(self, parent):
        log_frame = ttk.LabelFrame(parent, text="📝 系統日誌與警報", padding="5")
        log_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=5, font=("Courier", 9))
        self.log_text.pack(fill=tk.X)
        
    def start_data_thread(self):
        """啟動數據讀取線程"""
        self.data_thread = threading.Thread(target=self.data_reader, daemon=True)
        self.data_thread.start()
    
    def data_reader(self):
        """數據讀取線程"""
        while True:
            if self.is_connected and self.serial_port and self.is_monitoring:
                try:
                    if self.serial_port.in_waiting:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        self.data_queue.put(('data', data))
                except Exception as e:
                    self.data_queue.put(('error', str(e)))
            time.sleep(0.01)
    
    def update_display(self):
        """更新顯示"""
        # 處理數據隊列
        while not self.data_queue.empty():
            try:
                msg_type, data = self.data_queue.get_nowait()
                if msg_type == 'data':
                    self.process_data(data)
                elif msg_type == 'error':
                    self.log(f"❌ 錯誤: {data}")
            except queue.Empty:
                break
        
        # 更新顯示內容
        self.update_realtime_display()
        self.update_stats_display()
        self.update_behavior_display()
        self.update_chart_display()
        
        # 繼續更新
        self.root.after(200, self.update_display)
    
    def process_data(self, data):
        """處理接收到的數據"""
        self.raw_buffer.extend(data)
        
        # 顯示原始數據
        hex_str = ' '.join([f'{b:02X}' for b in data])
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.add_text(self.raw_text, f"[{timestamp}] {hex_str}\n")
        
        # 分析數據幀
        self.analyze_data()
    
    def analyze_data(self):
        """分析數據 - 增強版本"""
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
                    self.parse_frame_enhanced(frame)
                    i = end_pos
                else:
                    i += 1
            else:
                i += 1
        
        # 清理緩衝區
        if len(self.raw_buffer) > 2000:
            self.raw_buffer = self.raw_buffer[-1000:]
    
    def parse_frame_enhanced(self, frame):
        """增強版數據幀解析"""
        if len(frame) < 23:
            return
        
        self.stats['total_frames'] += 1
        
        # 解析數據
        frame_header = frame[0:4]
        data_len = (frame[5] << 8) | frame[4]
        data_type = frame[6]
        head_check = frame[7]
        
        target_state = frame[8]
        move_dist = (frame[10] << 8) | frame[9]
        move_energy = frame[11]
        still_dist = (frame[13] << 8) | frame[12]
        still_energy = frame[14]
        detect_dist = (frame[16] << 8) | frame[15]
        
        # 光感值
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
        self.analyze_behavior(target_state, detect_dist)
        
        # 更新當前數據
        self.current_data = {
            'timestamp': datetime.now(),
            'state': target_state,
            'move_dist': move_dist,
            'move_energy': move_energy,
            'still_dist': still_dist,
            'still_energy': still_energy,
            'detect_dist': detect_dist,
            'light': light_value,
            'frame_len': len(frame),
            'data_type': data_type
        }
        
        # 獲取狀態文字
        state_text = self.get_state_text(target_state)
        
        # 顯示詳細解析結果
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        result = f"""[{timestamp}] 數據幀 #{self.stats['total_frames']}
幀長度: {len(frame)} 字節  數據類型: 0x{data_type:02X}
目標狀態: {state_text} (0x{target_state:02X})
移動距離: {move_dist:4d} cm  能量: {move_energy:3d}
靜止距離: {still_dist:4d} cm  能量: {still_energy:3d}
檢測距離: {detect_dist:4d} cm  光感: {light_value:3d}
{"="*50}
"""
        self.add_text(self.parsed_text, result)
        
        # 檢查警報
        self.check_alerts(detect_dist, move_energy, still_energy, target_state)
    
    def update_statistics(self, state, move_dist, move_energy, still_dist, still_energy, detect_dist):
        """更新統計數據"""
        if state & 0x01:  # 有目標
            if state & 0x02:  # 移動目標
                self.stats['moving_detections'] += 1
            if state & 0x04:  # 靜止目標
                self.stats['still_detections'] += 1
        else:
            self.stats['no_target'] += 1
        
        # 更新距離統計
        if detect_dist > 0:
            self.stats['max_distance'] = max(self.stats['max_distance'], detect_dist)
            if self.stats['min_distance'] == 9999:
                self.stats['min_distance'] = detect_dist
            else:
                self.stats['min_distance'] = min(self.stats['min_distance'], detect_dist)
        
        # 更新能量統計
        if len(self.data_history['moving_energy']) > 0:
            self.stats['avg_moving_energy'] = sum(self.data_history['moving_energy']) / len(self.data_history['moving_energy'])
            self.stats['avg_still_energy'] = sum(self.data_history['still_energy']) / len(self.data_history['still_energy'])
        
        self.stats['last_update'] = time.time()
    
    def analyze_behavior(self, state, distance):
        """行為分析"""
        # 記錄狀態變化
        self.behavior['state_changes'].append(state)
        
        # 記錄距離變化
        if distance > 0:
            self.behavior['last_distances'].append(distance)
            
            # 分析距離趨勢
            if len(self.behavior['last_distances']) >= 5:
                recent = list(self.behavior['last_distances'])[-5:]
                trend = recent[-1] - recent[0]
                
                if trend < -50:  # 接近超過50cm
                    self.behavior['approach_count'] += 1
                    self.log("📍 檢測到接近行為")
                elif trend > 50:  # 遠離超過50cm
                    self.behavior['leave_count'] += 1
                    self.log("📍 檢測到離開行為")
                elif abs(trend) < 20:  # 穩定
                    self.behavior['stable_count'] += 1
        
        # 檢測雜訊
        if len(self.behavior['state_changes']) >= 10:
            recent_states = list(self.behavior['state_changes'])[-10:]
            changes = sum(1 for i in range(1, len(recent_states)) 
                         if recent_states[i] != recent_states[i-1])
            if changes > 6:
                self.behavior['noise_count'] += 1
    
    def check_alerts(self, distance, move_energy, still_energy, state):
        """檢查警報"""
        alerts = []
        
        # 近距離警報
        if 0 < distance < 50:
            alerts.append(f"⚠️ 近距離警報: {distance}cm")
        
        # 高能量警報
        if move_energy > 80:
            alerts.append(f"⚡ 高移動能量: {move_energy}")
        if still_energy > 80:
            alerts.append(f"⚡ 高靜止能量: {still_energy}")
        
        # 異常狀態警報
        if state > 7:  # 超出正常範圍
            alerts.append(f"🚨 異常狀態碼: 0x{state:02X}")
        
        # 顯示警報
        for alert in alerts:
            self.log(alert)
    
    def get_state_text(self, state):
        """獲取狀態文字描述"""
        if state & 0x01:
            text = ""
            if state & 0x02:
                text += "🏃 移動目標 "
            if state & 0x04:
                text += "🧍 靜止目標"
            return text.strip()
        else:
            return "❌ 無目標"
    
    def update_realtime_display(self):
        """更新即時數據顯示"""
        if self.current_data:
            data = self.current_data
            state_text = self.get_state_text(data['state'])
            
            realtime_info = f"""╔══════════════════════════════════════════════════╗
║                   即時數據分析                     ║
╠══════════════════════════════════════════════════╣
║ 目標狀態: {state_text:<30} ║
║ 移動距離: {data['move_dist']:4d} cm    移動能量: {data['move_energy']:3d}     ║
║ 靜止距離: {data['still_dist']:4d} cm    靜止能量: {data['still_energy']:3d}     ║
║ 檢測距離: {data['detect_dist']:4d} cm    光感值:  {data['light']:3d}     ║
║                                                  ║
║ 數據幀長: {data['frame_len']:2d} 字節   數據類型: 0x{data['data_type']:02X}       ║
║ 最後更新: {data['timestamp'].strftime('%H:%M:%S.%f')[:-3]:<30} ║
╚══════════════════════════════════════════════════╝"""
        else:
            realtime_info = """╔══════════════════════════════════════════════════╗
║                   即時數據分析                     ║
╠══════════════════════════════════════════════════╣
║ 目標狀態: 等待數據...                            ║
║ 移動距離:   -- cm    移動能量:  --              ║
║ 靜止距離:   -- cm    靜止能量:  --              ║
║ 檢測距離:   -- cm    光感值:   --              ║
║                                                  ║
║ 請先連接設備並開始監控                           ║
╚══════════════════════════════════════════════════╝"""
        
        self.realtime_text.delete(1.0, tk.END)
        self.realtime_text.insert(1.0, realtime_info)
    
    def update_stats_display(self):
        """更新統計顯示"""
        runtime = time.time() - self.stats['start_time']
        total = self.stats['total_frames']
        
        if total > 0:
            moving_rate = (self.stats['moving_detections'] / total) * 100
            still_rate = (self.stats['still_detections'] / total) * 100
            no_target_rate = (self.stats['no_target'] / total) * 100
            fps = total / max(runtime, 1)
            
            stats_info = f"""╔════════════════════════════════════════╗
║              統計分析報告                ║
╠════════════════════════════════════════╣
║ 總數據幀: {total:<8} 運行時間: {int(runtime):>4}秒 ║
║ 平均幀率: {fps:>6.1f} 幀/秒                ║
║                                        ║
║ 檢測統計:                              ║
║   移動檢測: {self.stats['moving_detections']:>4} ({moving_rate:>5.1f}%)        ║
║   靜止檢測: {self.stats['still_detections']:>4} ({still_rate:>5.1f}%)        ║
║   無目標:   {self.stats['no_target']:>4} ({no_target_rate:>5.1f}%)        ║
║                                        ║
║ 距離統計:                              ║
║   最大距離: {self.stats['max_distance']:>4} cm                ║
║   最小距離: {self.stats['min_distance'] if self.stats['min_distance'] != 9999 else 0:>4} cm                ║
║                                        ║
║ 能量統計:                              ║
║   平均移動: {self.stats['avg_moving_energy']:>6.1f}              ║
║   平均靜止: {self.stats['avg_still_energy']:>6.1f}              ║
╚════════════════════════════════════════╝"""
        else:
            stats_info = """╔════════════════════════════════════════╗
║              統計分析報告                ║
╠════════════════════════════════════════╣
║ 等待數據...                            ║
║                                        ║
║ 請先連接設備並發送啟動命令               ║
╚════════════════════════════════════════╝"""
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_info)
        
        # 更新頂部狀態
        self.frame_count_label.config(text=f"數據幀: {total}")
        self.fps_label.config(text=f"幀率: {total/max(runtime,1):.1f}/s")
    
    def update_behavior_display(self):
        """更新行為分析顯示"""
        total_behaviors = (self.behavior['approach_count'] + 
                          self.behavior['leave_count'] + 
                          self.behavior['stable_count'])
        
        if total_behaviors > 0:
            behavior_info = f"""╔══════════════════════════════════════╗
║            行為模式分析                ║
╠══════════════════════════════════════╣
║ 接近行為: {self.behavior['approach_count']:>3} 次               ║
║ 離開行為: {self.behavior['leave_count']:>3} 次               ║
║ 穩定行為: {self.behavior['stable_count']:>3} 次               ║
║ 雜訊干擾: {self.behavior['noise_count']:>3} 次               ║
║                                      ║
║ 主要行為: {self.get_dominant_behavior():<16} ║
║ 建議: {self.get_behavior_recommendation():<20} ║
╚══════════════════════════════════════╝"""
        else:
            behavior_info = """╔══════════════════════════════════════╗
║            行為模式分析                ║
╠══════════════════════════════════════╣
║ 等待足夠的數據進行分析...              ║
╚══════════════════════════════════════╝"""
        
        self.behavior_text.delete(1.0, tk.END)
        self.behavior_text.insert(1.0, behavior_info)
    
    def get_dominant_behavior(self):
        """獲取主要行為"""
        behaviors = {
            '接近行為': self.behavior['approach_count'],
            '離開行為': self.behavior['leave_count'],
            '穩定存在': self.behavior['stable_count'],
            '環境干擾': self.behavior['noise_count']
        }
        return max(behaviors, key=behaviors.get) if any(behaviors.values()) else "數據不足"
    
    def get_behavior_recommendation(self):
        """獲取行為建議"""
        if self.behavior['noise_count'] > 5:
            return "調整靈敏度"
        elif self.behavior['approach_count'] > self.behavior['leave_count']:
            return "適合入口監控"
        elif self.behavior['stable_count'] > 10:
            return "適合存在檢測"
        else:
            return "持續監控中"
    
    def update_chart_display(self):
        """更新圖表顯示"""
        if len(self.data_history['detection_distance']) < 5:
            return
        
        # 獲取最近30個數據點
        data = list(self.data_history['detection_distance'])[-30:]
        if not data or max(data) == 0:
            return
        
        max_val = max(data)
        min_val = min([d for d in data if d > 0]) if any(d > 0 for d in data) else 0
        height = 15
        
        chart = f"""距離趨勢圖 (最近{len(data)}個數據點)
最大值: {max_val} cm  最小值: {min_val} cm
{'='*60}
"""
        
        # 繪製圖表
        for h in range(height, 0, -1):
            threshold = min_val + (max_val - min_val) * h / height
            line = f"{threshold:4.0f} |"
            for val in data:
                if val >= threshold:
                    line += "█"
                elif val > 0:
                    line += "░"
                else:
                    line += " "
            chart += line + "\n"
        
        chart += "     " + "-" * len(data) + "\n"
        chart += "     " + "".join([str(i % 10) for i in range(len(data))]) + "\n"
        chart += "\n█ = 檢測到目標  ░ = 低於閾值  空白 = 無目標"
        
        self.chart_text.delete(1.0, tk.END)
        self.chart_text.insert(1.0, chart)
    
    def add_text(self, widget, text):
        """添加文字到文本框"""
        widget.insert(tk.END, text)
        widget.see(tk.END)
        
        # 限制行數
        lines = widget.get("1.0", tk.END).split('\n')
        if len(lines) > 200:
            widget.delete("1.0", f"{len(lines)-100}.0")
    
    def toggle_connection(self):
        """切換連接狀態"""
        if not self.is_connected:
            try:
                self.port_name = self.port_var.get()
                self.serial_port = serial.Serial(self.port_name, self.baud_rate, timeout=1)
                self.is_connected = True
                self.connect_btn.config(text="🔌 斷開")
                self.status_label.config(text="🟢 已連接", foreground="green")
                self.log(f"✅ 成功連接到 {self.port_name}")
            except Exception as e:
                self.log(f"❌ 連接失敗: {e}")
                messagebox.showerror("連接錯誤", f"無法連接到串列埠\n{e}")
        else:
            if self.serial_port:
                self.serial_port.close()
            self.is_connected = False
            self.is_monitoring = False
            self.connect_btn.config(text="🔌 連接")
            self.monitor_btn.config(text="▶️ 開始監控")
            self.status_label.config(text="🔴 未連接", foreground="red")
            self.log("已斷開連接")
    
    def toggle_monitoring(self):
        """切換監控狀態"""
        if not self.is_connected:
            messagebox.showwarning("警告", "請先連接串列埠")
            return
        
        self.is_monitoring = not self.is_monitoring
        if self.is_monitoring:
            self.monitor_btn.config(text="⏹️ 停止監控")
            self.log("🔍 開始監控數據...")
        else:
            self.monitor_btn.config(text="▶️ 開始監控")
            self.log("⏹️ 停止監控")
    
    def send_command(self, hex_string):
        """發送命令"""
        if not self.is_connected:
            messagebox.showwarning("警告", "請先連接串列埠")
            return
        
        try:
            cmd = bytes.fromhex(hex_string.replace(" ", ""))
            self.serial_port.write(cmd)
            self.serial_port.flush()
            self.log(f"📤 已發送: {hex_string}")
        except Exception as e:
            self.log(f"❌ 發送失敗: {e}")
            messagebox.showerror("發送錯誤", f"命令發送失敗\n{e}")
    
    def send_custom_command(self):
        """發送自定義命令"""
        hex_string = self.custom_cmd_var.get().strip()
        if not hex_string:
            messagebox.showwarning("警告", "請輸入16進制命令")
            return
        
        self.send_command(hex_string)
        self.custom_cmd_var.set("")
    
    def clear_data(self):
        """清除數據"""
        # 清除顯示
        self.raw_text.delete(1.0, tk.END)
        self.parsed_text.delete(1.0, tk.END)
        self.chart_text.delete(1.0, tk.END)
        
        # 清除歷史數據
        for key in self.data_history:
            self.data_history[key].clear()
        
        # 重置統計
        self.stats = {
            'total_frames': 0,
            'moving_detections': 0,
            'still_detections': 0,
            'no_target': 0,
            'start_time': time.time(),
            'max_distance': 0,
            'min_distance': 9999,
            'avg_moving_energy': 0,
            'avg_still_energy': 0,
            'last_update': time.time()
        }
        
        # 重置行為分析
        for key in self.behavior:
            if isinstance(self.behavior[key], deque):
                self.behavior[key].clear()
            else:
                self.behavior[key] = 0
        
        self.current_data = None
        self.log("🗑️ 已清除所有數據")
    
    def log(self, message):
        """記錄日誌"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}\n"
        self.add_text(self.log_text, log_entry)
    
    def run(self):
        """運行程序"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            if self.is_connected and self.serial_port:
                self.serial_port.close()

def main():
    print("啟動LD2412增強版GUI控制系統...")
    app = EnhancedLD2412GUI()
    app.run()

if __name__ == "__main__":
    main() 