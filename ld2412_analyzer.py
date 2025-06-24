#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext
import serial
import threading
import time
import queue
from datetime import datetime
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from collections import deque

class LD2412Analyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("LD2412 雷達數據分析系統")
        self.root.geometry("1400x900")
        
        # 串列埠設定
        self.serial_port = None
        self.port_name = "/dev/cu.usbserial-0001"
        self.baud_rate = 115200
        self.is_connected = False
        self.is_monitoring = False
        
        # 數據處理
        self.data_queue = queue.Queue()
        self.raw_buffer = bytearray()
        
        # 數據分析變數
        self.data_history = {
            'time': deque(maxlen=100),
            'moving_distance': deque(maxlen=100),
            'moving_energy': deque(maxlen=100),
            'still_distance': deque(maxlen=100),
            'still_energy': deque(maxlen=100),
            'detection_distance': deque(maxlen=100),
            'target_state': deque(maxlen=100)
        }
        
        # 統計數據
        self.stats = {
            'total_frames': 0,
            'moving_detections': 0,
            'still_detections': 0,
            'no_target': 0,
            'avg_moving_distance': 0,
            'avg_still_distance': 0,
            'max_distance': 0,
            'min_distance': 9999
        }
        
        # 數據模式分析
        self.patterns = {
            'approach': 0,  # 接近模式
            'leave': 0,     # 離開模式
            'stable': 0,    # 穩定模式
            'noise': 0      # 雜訊
        }
        
        self.setup_ui()
        self.start_threads()
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 1. 控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="5")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 連接控制
        ttk.Label(control_frame, text="串列埠:").grid(row=0, column=0, padx=5)
        self.port_var = tk.StringVar(value=self.port_name)
        port_entry = ttk.Entry(control_frame, textvariable=self.port_var, width=20)
        port_entry.grid(row=0, column=1, padx=5)
        
        self.connect_btn = ttk.Button(control_frame, text="連接", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=2, padx=5)
        
        self.monitor_btn = ttk.Button(control_frame, text="開始監控", command=self.toggle_monitoring)
        self.monitor_btn.grid(row=0, column=3, padx=5)
        
        ttk.Button(control_frame, text="發送啟動命令", command=self.send_start_command).grid(row=0, column=4, padx=5)
        ttk.Button(control_frame, text="清除數據", command=self.clear_data).grid(row=0, column=5, padx=5)
        
        self.status_label = ttk.Label(control_frame, text="未連接", foreground="red")
        self.status_label.grid(row=0, column=6, padx=20)
        
        # 2. 主要內容區域
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)
        
        # 左側 - 數據分析面板
        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_frame.rowconfigure(2, weight=1)
        
        # 即時數據顯示
        realtime_frame = ttk.LabelFrame(left_frame, text="即時數據", padding="10")
        realtime_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.realtime_labels = {}
        labels = [
            ("目標狀態", "target_state"),
            ("移動距離", "moving_distance"),
            ("移動能量", "moving_energy"),
            ("靜止距離", "still_distance"),
            ("靜止能量", "still_energy"),
            ("檢測距離", "detection_distance")
        ]
        
        for i, (text, key) in enumerate(labels):
            ttk.Label(realtime_frame, text=f"{text}:").grid(row=i, column=0, sticky=tk.W, pady=2)
            self.realtime_labels[key] = ttk.Label(realtime_frame, text="--", font=("Arial", 12, "bold"))
            self.realtime_labels[key].grid(row=i, column=1, sticky=tk.W, padx=10, pady=2)
        
        # 統計數據顯示
        stats_frame = ttk.LabelFrame(left_frame, text="統計分析", padding="10")
        stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.stats_text = tk.Text(stats_frame, height=8, width=40, font=("Courier", 10))
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 模式分析
        pattern_frame = ttk.LabelFrame(left_frame, text="行為模式分析", padding="10")
        pattern_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.pattern_text = tk.Text(pattern_frame, height=10, width=40, font=("Courier", 10))
        self.pattern_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 右側 - 圖形顯示
        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # 距離趨勢圖
        distance_frame = ttk.LabelFrame(right_frame, text="距離趨勢分析", padding="5")
        distance_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        
        self.fig1 = Figure(figsize=(8, 3), dpi=80)
        self.ax1 = self.fig1.add_subplot(111)
        self.ax1.set_xlabel('時間 (秒)')
        self.ax1.set_ylabel('距離 (cm)')
        self.ax1.set_title('目標距離變化趨勢')
        self.ax1.grid(True)
        
        self.canvas1 = FigureCanvasTkAgg(self.fig1, distance_frame)
        self.canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 能量分布圖
        energy_frame = ttk.LabelFrame(right_frame, text="能量分布分析", padding="5")
        energy_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.fig2 = Figure(figsize=(8, 3), dpi=80)
        self.ax2 = self.fig2.add_subplot(111)
        self.ax2.set_xlabel('時間 (秒)')
        self.ax2.set_ylabel('能量值')
        self.ax2.set_title('移動/靜止能量分布')
        self.ax2.grid(True)
        
        self.canvas2 = FigureCanvasTkAgg(self.fig2, energy_frame)
        self.canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 3. 日誌區域
        log_frame = ttk.LabelFrame(main_frame, text="分析日誌", padding="5")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, font=("Courier", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 初始化顯示
        self.update_stats_display()
        self.log("系統啟動，等待連接...")
        
    def start_threads(self):
        # 數據讀取線程
        self.data_thread = threading.Thread(target=self.data_reader, daemon=True)
        self.data_thread.start()
        
        # UI更新定時器
        self.update_ui()
        self.update_graphs()
        
    def data_reader(self):
        while True:
            if self.is_connected and self.serial_port and self.is_monitoring:
                try:
                    if self.serial_port.in_waiting:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        self.data_queue.put(('data', data))
                except Exception as e:
                    self.data_queue.put(('error', str(e)))
            time.sleep(0.01)
    
    def update_ui(self):
        # 處理數據隊列
        while not self.data_queue.empty():
            try:
                msg_type, data = self.data_queue.get_nowait()
                if msg_type == 'data':
                    self.process_received_data(data)
                elif msg_type == 'error':
                    self.log(f"錯誤: {data}")
            except queue.Empty:
                break
        
        # 更新顯示
        self.update_realtime_display()
        self.update_stats_display()
        self.update_pattern_analysis()
        
        # 繼續更新
        self.root.after(100, self.update_ui)
    
    def update_graphs(self):
        if len(self.data_history['time']) > 0:
            # 更新距離趨勢圖
            self.ax1.clear()
            self.ax1.plot(self.data_history['time'], self.data_history['moving_distance'], 
                         'b-', label='移動距離', linewidth=2)
            self.ax1.plot(self.data_history['time'], self.data_history['still_distance'], 
                         'r-', label='靜止距離', linewidth=2)
            self.ax1.plot(self.data_history['time'], self.data_history['detection_distance'], 
                         'g--', label='檢測距離', linewidth=1)
            self.ax1.set_xlabel('時間 (秒)')
            self.ax1.set_ylabel('距離 (cm)')
            self.ax1.set_title('目標距離變化趨勢')
            self.ax1.legend()
            self.ax1.grid(True)
            self.canvas1.draw()
            
            # 更新能量分布圖
            self.ax2.clear()
            self.ax2.plot(self.data_history['time'], self.data_history['moving_energy'], 
                         'b-', label='移動能量', linewidth=2)
            self.ax2.plot(self.data_history['time'], self.data_history['still_energy'], 
                         'r-', label='靜止能量', linewidth=2)
            self.ax2.set_xlabel('時間 (秒)')
            self.ax2.set_ylabel('能量值')
            self.ax2.set_title('移動/靜止能量分布')
            self.ax2.legend()
            self.ax2.grid(True)
            self.canvas2.draw()
        
        # 繼續更新
        self.root.after(500, self.update_graphs)
    
    def process_received_data(self, data):
        self.raw_buffer.extend(data)
        
        # 分析數據幀
        self.analyze_frames()
    
    def analyze_frames(self):
        buffer = bytes(self.raw_buffer)
        
        # 查找數據幀 F4 F3 F2 F1 ... F8 F7 F6 F5
        i = 0
        while i < len(buffer) - 7:
            if (buffer[i:i+4] == b'\xF4\xF3\xF2\xF1'):
                # 找到數據幀開頭
                end_pos = -1
                for j in range(i + 8, len(buffer) - 3):
                    if buffer[j:j+4] == b'\xF8\xF7\xF6\xF5':
                        end_pos = j + 4
                        break
                
                if end_pos != -1:
                    frame = buffer[i:end_pos]
                    self.parse_and_analyze_frame(frame)
                    i = end_pos
                else:
                    i += 1
            else:
                i += 1
        
        # 清理已處理的數據
        if len(self.raw_buffer) > 1000:
            self.raw_buffer = self.raw_buffer[-500:]
    
    def parse_and_analyze_frame(self, frame):
        if len(frame) < 23:
            return
        
        # 解析數據
        target_state = frame[8]
        move_dist = (frame[10] << 8) | frame[9]
        move_energy = frame[11]
        still_dist = (frame[13] << 8) | frame[12]
        still_energy = frame[14]
        detect_dist = (frame[16] << 8) | frame[15]
        
        # 儲存到歷史記錄
        current_time = len(self.data_history['time']) * 0.1  # 假設每0.1秒一個數據點
        self.data_history['time'].append(current_time)
        self.data_history['moving_distance'].append(move_dist)
        self.data_history['moving_energy'].append(move_energy)
        self.data_history['still_distance'].append(still_dist)
        self.data_history['still_energy'].append(still_energy)
        self.data_history['detection_distance'].append(detect_dist)
        self.data_history['target_state'].append(target_state)
        
        # 更新統計
        self.stats['total_frames'] += 1
        
        if target_state & 0x01:  # 有目標
            if target_state & 0x02:  # 移動目標
                self.stats['moving_detections'] += 1
            if target_state & 0x04:  # 靜止目標
                self.stats['still_detections'] += 1
        else:
            self.stats['no_target'] += 1
        
        # 更新最大最小距離
        if detect_dist > 0:
            self.stats['max_distance'] = max(self.stats['max_distance'], detect_dist)
            self.stats['min_distance'] = min(self.stats['min_distance'], detect_dist)
        
        # 分析行為模式
        self.analyze_patterns()
        
        # 記錄重要事件
        if target_state & 0x01:
            if move_energy > 80:
                self.log(f"⚡ 高能量移動檢測: {move_dist}cm, 能量:{move_energy}")
            elif still_energy > 80:
                self.log(f"🔍 高能量靜止檢測: {still_dist}cm, 能量:{still_energy}")
    
    def analyze_patterns(self):
        if len(self.data_history['detection_distance']) < 10:
            return
        
        # 分析最近10個數據點的趨勢
        recent_distances = list(self.data_history['detection_distance'])[-10:]
        recent_states = list(self.data_history['target_state'])[-10:]
        
        # 計算距離變化趨勢
        if all(d > 0 for d in recent_distances):
            distance_diff = recent_distances[-1] - recent_distances[0]
            
            if distance_diff < -50:  # 接近超過50cm
                self.patterns['approach'] += 1
                self.log("📍 檢測到接近模式")
            elif distance_diff > 50:  # 遠離超過50cm
                self.patterns['leave'] += 1
                self.log("📍 檢測到離開模式")
            else:
                self.patterns['stable'] += 1
        
        # 檢測雜訊
        state_changes = sum(1 for i in range(1, len(recent_states)) 
                           if recent_states[i] != recent_states[i-1])
        if state_changes > 5:
            self.patterns['noise'] += 1
    
    def update_realtime_display(self):
        if len(self.data_history['target_state']) > 0:
            # 獲取最新數據
            latest_state = self.data_history['target_state'][-1]
            
            # 更新目標狀態
            state_text = "無目標"
            if latest_state & 0x01:
                state_text = ""
                if latest_state & 0x02:
                    state_text += "移動 "
                if latest_state & 0x04:
                    state_text += "靜止"
            
            self.realtime_labels['target_state'].config(text=state_text)
            self.realtime_labels['moving_distance'].config(
                text=f"{self.data_history['moving_distance'][-1]} cm")
            self.realtime_labels['moving_energy'].config(
                text=f"{self.data_history['moving_energy'][-1]}")
            self.realtime_labels['still_distance'].config(
                text=f"{self.data_history['still_distance'][-1]} cm")
            self.realtime_labels['still_energy'].config(
                text=f"{self.data_history['still_energy'][-1]}")
            self.realtime_labels['detection_distance'].config(
                text=f"{self.data_history['detection_distance'][-1]} cm")
    
    def update_stats_display(self):
        self.stats_text.delete(1.0, tk.END)
        
        total = self.stats['total_frames']
        if total > 0:
            moving_rate = (self.stats['moving_detections'] / total) * 100
            still_rate = (self.stats['still_detections'] / total) * 100
            no_target_rate = (self.stats['no_target'] / total) * 100
            
            stats_info = f"""總數據幀: {total}
移動檢測: {self.stats['moving_detections']} ({moving_rate:.1f}%)
靜止檢測: {self.stats['still_detections']} ({still_rate:.1f}%)
無目標: {self.stats['no_target']} ({no_target_rate:.1f}%)

距離範圍: {self.stats['min_distance']} - {self.stats['max_distance']} cm

平均移動距離: {self.calculate_average('moving_distance'):.1f} cm
平均靜止距離: {self.calculate_average('still_distance'):.1f} cm"""
            
            self.stats_text.insert(tk.END, stats_info)
    
    def update_pattern_analysis(self):
        self.pattern_text.delete(1.0, tk.END)
        
        total_patterns = sum(self.patterns.values())
        if total_patterns > 0:
            pattern_info = f"""行為模式統計:

接近模式: {self.patterns['approach']} 次
離開模式: {self.patterns['leave']} 次
穩定模式: {self.patterns['stable']} 次
雜訊干擾: {self.patterns['noise']} 次

主要行為: {self.get_dominant_pattern()}

建議:
{self.get_recommendations()}"""
            
            self.pattern_text.insert(tk.END, pattern_info)
    
    def get_dominant_pattern(self):
        if not any(self.patterns.values()):
            return "數據不足"
        
        dominant = max(self.patterns, key=self.patterns.get)
        patterns_cn = {
            'approach': '接近行為',
            'leave': '離開行為',
            'stable': '穩定存在',
            'noise': '環境干擾'
        }
        return patterns_cn.get(dominant, "未知")
    
    def get_recommendations(self):
        if self.patterns['noise'] > sum(self.patterns.values()) * 0.3:
            return "• 環境干擾較大，建議調整靈敏度\n• 檢查是否有其他電子設備干擾"
        elif self.patterns['approach'] > self.patterns['leave']:
            return "• 檢測區域活動頻繁\n• 適合用於入口監控"
        elif self.patterns['stable'] > sum(self.patterns.values()) * 0.5:
            return "• 目標相對穩定\n• 適合用於存在檢測"
        else:
            return "• 運行正常\n• 持續監控中"
    
    def calculate_average(self, key):
        if len(self.data_history[key]) == 0:
            return 0
        values = [v for v in self.data_history[key] if v > 0]
        return sum(values) / len(values) if values else 0
    
    def toggle_connection(self):
        if not self.is_connected:
            try:
                self.port_name = self.port_var.get()
                self.serial_port = serial.Serial(self.port_name, self.baud_rate, timeout=1)
                self.is_connected = True
                self.connect_btn.config(text="斷開")
                self.status_label.config(text="已連接", foreground="green")
                self.log(f"✅ 成功連接到 {self.port_name}")
            except Exception as e:
                self.log(f"❌ 連接失敗: {e}")
        else:
            if self.serial_port:
                self.serial_port.close()
            self.is_connected = False
            self.is_monitoring = False
            self.connect_btn.config(text="連接")
            self.monitor_btn.config(text="開始監控")
            self.status_label.config(text="未連接", foreground="red")
            self.log("已斷開連接")
    
    def toggle_monitoring(self):
        if not self.is_connected:
            self.log("⚠️  請先連接串列埠")
            return
        
        self.is_monitoring = not self.is_monitoring
        if self.is_monitoring:
            self.monitor_btn.config(text="停止監控")
            self.log("🔍 開始監控數據...")
        else:
            self.monitor_btn.config(text="開始監控")
            self.log("⏹️  停止監控")
    
    def send_start_command(self):
        if not self.is_connected:
            self.log("⚠️  請先連接串列埠")
            return
        
        try:
            # 發送開始數據輸出命令
            cmd = bytes.fromhex("FD FC FB FA 02 00 12 00 04 03 02 01")
            self.serial_port.write(cmd)
            self.serial_port.flush()
            self.log("📤 已發送啟動命令")
        except Exception as e:
            self.log(f"❌ 發送失敗: {e}")
    
    def clear_data(self):
        # 清除歷史數據
        for key in self.data_history:
            self.data_history[key].clear()
        
        # 重置統計
        self.stats = {
            'total_frames': 0,
            'moving_detections': 0,
            'still_detections': 0,
            'no_target': 0,
            'avg_moving_distance': 0,
            'avg_still_distance': 0,
            'max_distance': 0,
            'min_distance': 9999
        }
        
        # 重置模式
        for key in self.patterns:
            self.patterns[key] = 0
        
        self.log("🗑️  已清除所有數據")
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

def main():
    # 設置matplotlib中文字體
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    root = tk.Tk()
    app = LD2412Analyzer(root)
    root.mainloop()

if __name__ == "__main__":
    main() 