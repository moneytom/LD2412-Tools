#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial
import threading
import time
import queue
from datetime import datetime
import os

# 消除macOS上的tkinter警告
os.environ['TK_SILENCE_DEPRECATION'] = '1'

class SimpleLD2412GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LD2412 雷達控制與分析系統")
        self.root.geometry("1000x700")
        
        # 串列埠設定
        self.port_name = "/dev/cu.usbserial-0001"
        self.baud_rate = 115200
        self.serial_port = None
        self.is_connected = False
        self.is_monitoring = False
        
        # 數據處理
        self.data_queue = queue.Queue()
        self.raw_buffer = bytearray()
        
        # 統計數據
        self.frame_count = 0
        self.start_time = time.time()
        
        self.create_widgets()
        self.start_data_thread()
        self.update_display()
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. 控制區域
        control_frame = ttk.LabelFrame(main_frame, text="🎛️ 控制面板", padding="10")
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
        
        # 命令按鈕
        cmd_frame = ttk.Frame(control_frame)
        cmd_frame.pack(fill=tk.X)
        
        # 常用命令按鈕
        commands = [
            ("🚀 啟動數據輸出", "FD FC FB FA 02 00 12 00 04 03 02 01"),
            ("📋 查詢版本", "FD FC FB FA 02 00 A0 00 04 03 02 01"),
            ("⚙️ 進入配置", "FD FC FB FA 04 00 FF 00 01 00 04 03 02 01"),
            ("🚪 退出配置", "FD FC FB FA 02 00 FE 00 04 03 02 01"),
            ("🔄 重啟", "FD FC FB FA 02 00 A3 00 04 03 02 01"),
            ("🗑️ 清除數據", None)
        ]
        
        for i, (name, cmd) in enumerate(commands):
            if cmd:
                btn = ttk.Button(cmd_frame, text=name, 
                               command=lambda c=cmd: self.send_command(c))
            else:
                btn = ttk.Button(cmd_frame, text=name, command=self.clear_data)
            btn.grid(row=i//3, column=i%3, padx=5, pady=2, sticky=tk.W)
        
        # 自定義命令
        custom_frame = ttk.Frame(control_frame)
        custom_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(custom_frame, text="自定義命令:").pack(side=tk.LEFT, padx=5)
        self.custom_cmd_var = tk.StringVar()
        ttk.Entry(custom_frame, textvariable=self.custom_cmd_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(custom_frame, text="📤 發送", command=self.send_custom_command).pack(side=tk.LEFT, padx=5)
        
        # 2. 數據顯示區域
        data_frame = ttk.Frame(main_frame)
        data_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左側 - 即時數據和統計
        left_frame = ttk.Frame(data_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 即時數據
        realtime_frame = ttk.LabelFrame(left_frame, text="📊 即時數據", padding="10")
        realtime_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.realtime_text = tk.Text(realtime_frame, height=8, font=("Courier", 11))
        self.realtime_text.pack(fill=tk.X)
        
        # 統計信息
        stats_frame = ttk.LabelFrame(left_frame, text="📈 統計信息", padding="10")
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_text = tk.Text(stats_frame, height=6, font=("Courier", 10))
        self.stats_text.pack(fill=tk.X)
        
        # 簡單圖表
        chart_frame = ttk.LabelFrame(left_frame, text="📉 距離趨勢", padding="10")
        chart_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chart_text = tk.Text(chart_frame, font=("Courier", 8))
        self.chart_text.pack(fill=tk.BOTH, expand=True)
        
        # 右側 - 16進制數據和解析
        right_frame = ttk.Frame(data_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 原始數據
        raw_frame = ttk.LabelFrame(right_frame, text="🔢 原始16進制數據", padding="5")
        raw_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.raw_text = scrolledtext.ScrolledText(raw_frame, font=("Courier", 9))
        self.raw_text.pack(fill=tk.BOTH, expand=True)
        
        # 解析結果
        parsed_frame = ttk.LabelFrame(right_frame, text="🔍 解析結果", padding="5")
        parsed_frame.pack(fill=tk.BOTH, expand=True)
        
        self.parsed_text = scrolledtext.ScrolledText(parsed_frame, font=("Courier", 9))
        self.parsed_text.pack(fill=tk.BOTH, expand=True)
        
        # 3. 日誌區域
        log_frame = ttk.LabelFrame(main_frame, text="📝 系統日誌", padding="5")
        log_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=5, font=("Courier", 9))
        self.log_text.pack(fill=tk.X)
        
        # 初始化
        self.log("🚀 系統啟動完成，請連接設備開始使用")
        self.update_realtime_display()
        
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
        
        # 繼續更新
        self.root.after(100, self.update_display)
    
    def process_data(self, data):
        """處理接收到的數據"""
        self.raw_buffer.extend(data)
        
        # 顯示原始數據
        hex_str = ' '.join([f'{b:02X}' for b in data])
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.add_text(self.raw_text, f"[{timestamp}] {hex_str}\n")
        
        # 分析數據幀
        self.analyze_data()
    
    def analyze_data(self):
        """分析數據"""
        buffer = bytes(self.raw_buffer)
        i = 0
        
        while i < len(buffer) - 7:
            # 查找數據幀頭
            if buffer[i:i+4] == b'\xF4\xF3\xF2\xF1':
                # 查找數據幀尾
                end_pos = -1
                for j in range(i + 8, min(i + 50, len(buffer) - 3)):
                    if buffer[j:j+4] == b'\xF8\xF7\xF6\xF5':
                        end_pos = j + 4
                        break
                
                if end_pos != -1:
                    frame = buffer[i:end_pos]
                    self.parse_frame(frame)
                    i = end_pos
                else:
                    i += 1
            else:
                i += 1
        
        # 清理緩衝區
        if len(self.raw_buffer) > 1000:
            self.raw_buffer = self.raw_buffer[-500:]
    
    def parse_frame(self, frame):
        """解析數據幀"""
        if len(frame) < 23:
            return
        
        self.frame_count += 1
        
        # 解析數據
        target_state = frame[8]
        move_dist = (frame[10] << 8) | frame[9]
        move_energy = frame[11]
        still_dist = (frame[13] << 8) | frame[12]
        still_energy = frame[14]
        detect_dist = (frame[16] << 8) | frame[15]
        
        # 獲取狀態文字
        if target_state & 0x01:
            state_text = ""
            if target_state & 0x02:
                state_text += "🏃 移動 "
            if target_state & 0x04:
                state_text += "🧍 靜止"
        else:
            state_text = "❌ 無目標"
        
        # 顯示解析結果
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = f"""[{timestamp}] 數據幀 #{self.frame_count}
目標狀態: {state_text}
移動距離: {move_dist:4d} cm  能量: {move_energy:3d}
靜止距離: {still_dist:4d} cm  能量: {still_energy:3d}
檢測距離: {detect_dist:4d} cm
{"="*40}
"""
        self.add_text(self.parsed_text, result)
        
        # 更新即時顯示
        self.current_data = {
            'state': state_text,
            'move_dist': move_dist,
            'move_energy': move_energy,
            'still_dist': still_dist,
            'still_energy': still_energy,
            'detect_dist': detect_dist
        }
        
        # 檢查警報
        if 0 < detect_dist < 50:
            self.log(f"⚠️ 近距離警報: {detect_dist}cm")
        if move_energy > 80 or still_energy > 80:
            self.log(f"⚡ 高能量檢測: 移動={move_energy} 靜止={still_energy}")
    
    def update_realtime_display(self):
        """更新即時數據顯示"""
        if hasattr(self, 'current_data'):
            data = self.current_data
            realtime_info = f"""目標狀態: {data['state']}
移動距離: {data['move_dist']:4d} cm    能量: {data['move_energy']:3d}
靜止距離: {data['still_dist']:4d} cm    能量: {data['still_energy']:3d}
檢測距離: {data['detect_dist']:4d} cm

最後更新: {datetime.now().strftime("%H:%M:%S")}"""
        else:
            realtime_info = """目標狀態: 等待數據...
移動距離:   -- cm    能量:  --
靜止距離:   -- cm    能量:  --
檢測距離:   -- cm

等待連接和數據..."""
        
        self.realtime_text.delete(1.0, tk.END)
        self.realtime_text.insert(1.0, realtime_info)
        
        # 更新統計
        runtime = int(time.time() - self.start_time)
        stats_info = f"""總數據幀: {self.frame_count}
運行時間: {runtime} 秒
平均幀率: {self.frame_count/max(runtime,1):.1f} 幀/秒

連接狀態: {"🟢 已連接" if self.is_connected else "🔴 未連接"}
監控狀態: {"🔍 監控中" if self.is_monitoring else "⏹️ 已停止"}"""
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_info)
        
        # 繼續更新
        self.root.after(1000, self.update_realtime_display)
    
    def add_text(self, widget, text):
        """添加文字到文本框"""
        widget.insert(tk.END, text)
        widget.see(tk.END)
        
        # 限制行數
        lines = widget.get("1.0", tk.END).split('\n')
        if len(lines) > 100:
            widget.delete("1.0", f"{len(lines)-50}.0")
    
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
        self.raw_text.delete(1.0, tk.END)
        self.parsed_text.delete(1.0, tk.END)
        self.chart_text.delete(1.0, tk.END)
        self.frame_count = 0
        self.start_time = time.time()
        if hasattr(self, 'current_data'):
            delattr(self, 'current_data')
        self.log("🗑️ 已清除所有數據")
    
    def log(self, message):
        """記錄日誌"""
        timestamp = datetime.now().strftime("%H:%M:%S")
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
    print("啟動LD2412 GUI控制系統...")
    app = SimpleLD2412GUI()
    app.run()

if __name__ == "__main__":
    main() 