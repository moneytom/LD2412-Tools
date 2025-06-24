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

# 設置環境變數來消除警告
os.environ['TK_SILENCE_DEPRECATION'] = '1'

class LD2412GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LD2412 雷達數據分析與控制系統")
        self.root.geometry("1200x800")
        
        # 串列埠設定
        self.port_name = "/dev/cu.usbserial-0001"
        self.baud_rate = 115200
        self.serial_port = None
        self.is_connected = False
        self.is_monitoring = False
        
        # 數據處理
        self.data_queue = queue.Queue()
        self.raw_buffer = bytearray()
        
        # 數據歷史
        self.data_history = {
            'time': deque(maxlen=50),
            'moving_distance': deque(maxlen=50),
            'moving_energy': deque(maxlen=50),
            'still_distance': deque(maxlen=50),
            'still_energy': deque(maxlen=50),
            'detection_distance': deque(maxlen=50),
            'target_state': deque(maxlen=50)
        }
        
        # 統計數據
        self.stats = {
            'total_frames': 0,
            'moving_detections': 0,
            'still_detections': 0,
            'no_target': 0,
            'start_time': time.time()
        }
        
        self.setup_gui()
        self.start_threads()
        
    def setup_gui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 1. 控制面板
        self.setup_control_panel(main_frame)
        
        # 2. 主要內容區域
        self.setup_main_content(main_frame)
        
        # 3. 日誌區域
        self.setup_log_area(main_frame)
        
    def setup_control_panel(self, parent):
        control_frame = ttk.LabelFrame(parent, text="🎛️ 控制面板", padding="10")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 連接控制
        ttk.Label(control_frame, text="串列埠:").grid(row=0, column=0, padx=5)
        self.port_var = tk.StringVar(value=self.port_name)
        port_entry = ttk.Entry(control_frame, textvariable=self.port_var, width=25)
        port_entry.grid(row=0, column=1, padx=5)
        
        self.connect_btn = ttk.Button(control_frame, text="🔌 連接", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=2, padx=5)
        
        self.monitor_btn = ttk.Button(control_frame, text="▶️ 開始監控", command=self.toggle_monitoring)
        self.monitor_btn.grid(row=0, column=3, padx=5)
        
        # 狀態顯示
        self.status_label = ttk.Label(control_frame, text="🔴 未連接", font=("Arial", 12, "bold"))
        self.status_label.grid(row=0, column=4, padx=20)
        
        # 命令按鈕區域
        cmd_frame = ttk.LabelFrame(control_frame, text="📤 命令控制", padding="5")
        cmd_frame.grid(row=1, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 預定義命令按鈕
        commands = [
            ("🚀 啟動數據輸出", "FD FC FB FA 02 00 12 00 04 03 02 01"),
            ("📋 查詢版本", "FD FC FB FA 02 00 A0 00 04 03 02 01"),
            ("⚙️ 進入配置模式", "FD FC FB FA 04 00 FF 00 01 00 04 03 02 01"),
            ("🚪 退出配置模式", "FD FC FB FA 02 00 FE 00 04 03 02 01"),
            ("🔄 重啟模組", "FD FC FB FA 02 00 A3 00 04 03 02 01"),
            ("🏭 恢復出廠設定", "FD FC FB FA 02 00 A2 00 04 03 02 01"),
            ("⏹️ 停止數據輸出", "FD FC FB FA 02 00 13 00 04 03 02 01")
        ]
        
        for i, (name, cmd) in enumerate(commands):
            btn = ttk.Button(cmd_frame, text=name, 
                           command=lambda c=cmd: self.send_command(c))
            btn.grid(row=i//4, column=i%4, padx=2, pady=2, sticky=(tk.W, tk.E))
        
        # 自定義命令
        custom_frame = ttk.Frame(cmd_frame)
        custom_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(custom_frame, text="自定義命令 (16進制):").grid(row=0, column=0, padx=5)
        self.custom_cmd_var = tk.StringVar()
        custom_entry = ttk.Entry(custom_frame, textvariable=self.custom_cmd_var, width=40)
        custom_entry.grid(row=0, column=1, padx=5)
        
        ttk.Button(custom_frame, text="📤 發送", 
                  command=self.send_custom_command).grid(row=0, column=2, padx=5)
        
        ttk.Button(control_frame, text="🗑️ 清除數據", 
                  command=self.clear_data).grid(row=0, column=5, padx=5)
        
    def setup_main_content(self, parent):
        content_frame = ttk.Frame(parent)
        content_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # 左側面板
        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_frame.rowconfigure(2, weight=1)
        
        # 即時數據
        realtime_frame = ttk.LabelFrame(left_frame, text="📊 即時數據", padding="10")
        realtime_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.realtime_labels = {}
        data_items = [
            ("目標狀態", "target_state"),
            ("移動距離", "moving_distance"),
            ("移動能量", "moving_energy"),
            ("靜止距離", "still_distance"),
            ("靜止能量", "still_energy"),
            ("檢測距離", "detection_distance")
        ]
        
        for i, (text, key) in enumerate(data_items):
            ttk.Label(realtime_frame, text=f"{text}:").grid(row=i, column=0, sticky=tk.W, pady=2)
            self.realtime_labels[key] = ttk.Label(realtime_frame, text="--", 
                                                font=("Arial", 12, "bold"), foreground="blue")
            self.realtime_labels[key].grid(row=i, column=1, sticky=tk.W, padx=10, pady=2)
        
        # 統計數據
        stats_frame = ttk.LabelFrame(left_frame, text="📈 統計分析", padding="10")
        stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.stats_text = tk.Text(stats_frame, height=8, width=40, font=("Courier", 10))
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 簡單圖表顯示
        chart_frame = ttk.LabelFrame(left_frame, text="📉 數據趨勢", padding="10")
        chart_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.chart_text = tk.Text(chart_frame, height=15, width=40, font=("Courier", 8))
        self.chart_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 右側面板 - 16進制數據
        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.rowconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # 原始數據
        raw_frame = ttk.LabelFrame(right_frame, text="🔢 原始16進制數據", padding="5")
        raw_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        
        self.raw_text = scrolledtext.ScrolledText(raw_frame, height=15, font=("Courier", 9))
        self.raw_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 解析結果
        parsed_frame = ttk.LabelFrame(right_frame, text="🔍 解析結果", padding="5")
        parsed_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.parsed_text = scrolledtext.ScrolledText(parsed_frame, height=15, font=("Courier", 9))
        self.parsed_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def setup_log_area(self, parent):
        log_frame = ttk.LabelFrame(parent, text="📝 系統日誌", padding="5")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, font=("Courier", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 初始化日誌
        self.log("🚀 系統啟動，等待連接...")
        
    def start_threads(self):
        # 數據讀取線程
        self.data_thread = threading.Thread(target=self.data_reader, daemon=True)
        self.data_thread.start()
        
        # UI更新定時器
        self.update_ui()
        
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
                    self.log(f"❌ 錯誤: {data}")
            except queue.Empty:
                break
        
        # 更新顯示
        self.update_displays()
        
        # 繼續更新
        self.root.after(100, self.update_ui)
    
    def process_received_data(self, data):
        self.raw_buffer.extend(data)
        
        # 顯示原始16進制數據
        hex_data = ' '.join([f'{b:02X}' for b in data])
        self.add_to_text_widget(self.raw_text, f"[{datetime.now().strftime('%H:%M:%S')}] {hex_data}\n")
        
        # 分析數據幀
        self.analyze_frames()
    
    def analyze_frames(self):
        buffer = bytes(self.raw_buffer)
        i = 0
        
        while i < len(buffer) - 7:
            if buffer[i:i+4] == b'\xF4\xF3\xF2\xF1':
                # 找到數據幀開頭
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
        if len(frame) < 23:
            return
        
        # 解析數據
        target_state = frame[8]
        move_dist = (frame[10] << 8) | frame[9]
        move_energy = frame[11]
        still_dist = (frame[13] << 8) | frame[12]
        still_energy = frame[14]
        detect_dist = (frame[16] << 8) | frame[15]
        
        # 保存到歷史記錄
        current_time = time.time() - self.stats['start_time']
        self.data_history['time'].append(current_time)
        self.data_history['moving_distance'].append(move_dist)
        self.data_history['moving_energy'].append(move_energy)
        self.data_history['still_distance'].append(still_dist)
        self.data_history['still_energy'].append(still_energy)
        self.data_history['detection_distance'].append(detect_dist)
        self.data_history['target_state'].append(target_state)
        
        # 更新統計
        self.stats['total_frames'] += 1
        if target_state & 0x01:
            if target_state & 0x02:
                self.stats['moving_detections'] += 1
            if target_state & 0x04:
                self.stats['still_detections'] += 1
        else:
            self.stats['no_target'] += 1
        
        # 顯示解析結果
        state_text = self.get_state_text(target_state)
        parse_result = f"""[{datetime.now().strftime('%H:%M:%S')}] 數據幀解析:
目標狀態: {state_text}
移動距離: {move_dist} cm (能量: {move_energy})
靜止距離: {still_dist} cm (能量: {still_energy})
檢測距離: {detect_dist} cm
---
"""
        self.add_to_text_widget(self.parsed_text, parse_result)
        
        # 檢查警報
        if 0 < detect_dist < 50:
            self.log(f"⚠️ 近距離警報: {detect_dist}cm")
        if move_energy > 80:
            self.log(f"⚡ 高移動能量: {move_energy}")
    
    def get_state_text(self, state):
        if state & 0x01:
            text = ""
            if state & 0x02:
                text += "🏃 移動目標 "
            if state & 0x04:
                text += "🧍 靜止目標"
            return text
        else:
            return "❌ 無目標"
    
    def update_displays(self):
        # 更新即時數據顯示
        if len(self.data_history['target_state']) > 0:
            latest_state = self.data_history['target_state'][-1]
            state_text = self.get_state_text(latest_state)
            
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
        
        # 更新統計顯示
        self.update_stats_display()
        
        # 更新圖表
        self.update_chart_display()
    
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

運行時間: {int(time.time() - self.stats['start_time'])}秒"""
            
            self.stats_text.insert(tk.END, stats_info)
    
    def update_chart_display(self):
        if len(self.data_history['detection_distance']) < 10:
            return
        
        self.chart_text.delete(1.0, tk.END)
        
        # 簡單的ASCII圖表
        data = list(self.data_history['detection_distance'])[-20:]
        if not data or max(data) == 0:
            return
        
        max_val = max(data)
        height = 10
        
        chart = "距離趨勢圖 (最近20個數據點):\n"
        chart += f"最大值: {max_val} cm\n\n"
        
        # 繪製圖表
        for h in range(height, 0, -1):
            line = f"{int(max_val * h / height):3d} |"
            for val in data:
                if val >= (max_val * h / height):
                    line += "█"
                else:
                    line += " "
            chart += line + "\n"
        
        chart += "    " + "-" * len(data) + "\n"
        chart += "    " + "".join([str(i % 10) for i in range(len(data))])
        
        self.chart_text.insert(tk.END, chart)
    
    def add_to_text_widget(self, widget, text):
        widget.insert(tk.END, text)
        widget.see(tk.END)
        
        # 限制文本長度
        lines = widget.get("1.0", tk.END).split('\n')
        if len(lines) > 100:
            widget.delete("1.0", f"{len(lines)-50}.0")
    
    def toggle_connection(self):
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
                messagebox.showerror("連接錯誤", f"無法連接到 {self.port_name}\n錯誤: {e}")
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
        if not self.is_connected:
            messagebox.showwarning("警告", "請先連接串列埠")
            return
        
        try:
            cmd = bytes.fromhex(hex_string.replace(" ", ""))
            self.serial_port.write(cmd)
            self.serial_port.flush()
            self.log(f"📤 已發送命令: {hex_string}")
        except Exception as e:
            self.log(f"❌ 發送失敗: {e}")
            messagebox.showerror("發送錯誤", f"命令發送失敗\n錯誤: {e}")
    
    def send_custom_command(self):
        hex_string = self.custom_cmd_var.get().strip()
        if not hex_string:
            messagebox.showwarning("警告", "請輸入16進制命令")
            return
        
        self.send_command(hex_string)
        self.custom_cmd_var.set("")  # 清空輸入框
    
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
            'start_time': time.time()
        }
        
        # 清除顯示
        self.raw_text.delete(1.0, tk.END)
        self.parsed_text.delete(1.0, tk.END)
        self.chart_text.delete(1.0, tk.END)
        
        self.log("🗑️ 已清除所有數據")
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.add_to_text_widget(self.log_text, log_entry)
    
    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.log("程序被中斷")
        finally:
            if self.is_connected and self.serial_port:
                self.serial_port.close()

def main():
    app = LD2412GUI()
    app.run()

if __name__ == "__main__":
    main() 