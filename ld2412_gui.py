#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial
import threading
import time
import queue
from datetime import datetime

class LD2412GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LD2412 雷達傳感器 - 圖形化控制介面")
        self.root.geometry("1200x800")
        
        # 串列埠設定
        self.serial_port = None
        self.port_name = "/dev/cu.usbserial-0001"
        self.baud_rate = 115200
        self.is_connected = False
        self.is_monitoring = False
        
        # 數據處理
        self.data_queue = queue.Queue()
        self.raw_buffer = bytearray()
        self.stats = {
            'total_bytes': 0,
            'data_frames': 0,
            'cmd_frames': 0
        }
        
        # 預定義命令
        self.predefined_commands = {
            "進入配置模式": "FD FC FB FA 04 00 FF 00 01 00 04 03 02 01",
            "退出配置模式": "FD FC FB FA 02 00 FE 00 04 03 02 01",
            "查詢版本": "FD FC FB FA 02 00 A0 00 04 03 02 01",
            "開始數據輸出": "FD FC FB FA 02 00 12 00 04 03 02 01",
            "查詢參數": "FD FC FB FA 02 00 61 00 04 03 02 01",
            "重啟模組": "FD FC FB FA 02 00 A3 00 04 03 02 01",
            "恢復出廠設定": "FD FC FB FA 02 00 A2 00 04 03 02 01"
        }
        
        self.setup_ui()
        self.start_data_thread()
        
        # 添加歡迎信息
        self.show_welcome_message()
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置網格權重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 1. 連接控制區域
        conn_frame = ttk.LabelFrame(main_frame, text="連接控制", padding="5")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(conn_frame, text="串列埠:").grid(row=0, column=0, padx=(0, 5))
        self.port_var = tk.StringVar(value=self.port_name)
        port_entry = ttk.Entry(conn_frame, textvariable=self.port_var, width=20)
        port_entry.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(conn_frame, text="波特率:").grid(row=0, column=2, padx=(0, 5))
        self.baud_var = tk.StringVar(value=str(self.baud_rate))
        baud_combo = ttk.Combobox(conn_frame, textvariable=self.baud_var, 
                                 values=["9600", "115200", "256000"], width=10)
        baud_combo.grid(row=0, column=3, padx=(0, 10))
        
        self.connect_btn = ttk.Button(conn_frame, text="連接", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=4, padx=(0, 10))
        
        self.status_label = ttk.Label(conn_frame, text="未連接", foreground="red")
        self.status_label.grid(row=0, column=5)
        
        # 2. 命令控制區域
        cmd_frame = ttk.LabelFrame(main_frame, text="命令控制", padding="5")
        cmd_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        cmd_frame.columnconfigure(1, weight=1)
        
        # 預定義命令
        ttk.Label(cmd_frame, text="預定義命令:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.cmd_var = tk.StringVar()
        cmd_combo = ttk.Combobox(cmd_frame, textvariable=self.cmd_var, 
                                values=list(self.predefined_commands.keys()), width=15)
        cmd_combo.grid(row=0, column=1, padx=(0, 10), sticky=(tk.W, tk.E))
        
        ttk.Button(cmd_frame, text="發送預定義", command=self.send_predefined_command).grid(row=0, column=2)
        
        # 自定義命令
        ttk.Label(cmd_frame, text="自定義命令:").grid(row=1, column=0, padx=(0, 5), sticky=tk.W, pady=(5, 0))
        self.custom_cmd_var = tk.StringVar()
        custom_entry = ttk.Entry(cmd_frame, textvariable=self.custom_cmd_var)
        custom_entry.grid(row=1, column=1, padx=(0, 10), sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(cmd_frame, text="發送自定義", command=self.send_custom_command).grid(row=1, column=2, pady=(5, 0))
        
        # 說明文字
        ttk.Label(cmd_frame, text="格式: FF FF FF FF (16進制，空格分隔)", 
                 font=("Arial", 8), foreground="gray").grid(row=2, column=1, sticky=tk.W, pady=(2, 0))
        
        # 3. 數據顯示區域
        display_frame = ttk.Frame(main_frame)
        display_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        display_frame.columnconfigure(0, weight=1)
        display_frame.columnconfigure(1, weight=1)
        display_frame.rowconfigure(0, weight=1)
        
        # 左側 - 原始數據
        raw_frame = ttk.LabelFrame(display_frame, text="原始16進制數據", padding="5")
        raw_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        raw_frame.columnconfigure(0, weight=1)
        raw_frame.rowconfigure(0, weight=1)
        
        self.raw_text = scrolledtext.ScrolledText(raw_frame, height=20, font=("Courier", 10))
        self.raw_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 右側 - 解析結果
        parsed_frame = ttk.LabelFrame(display_frame, text="數據解析結果", padding="5")
        parsed_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        parsed_frame.columnconfigure(0, weight=1)
        parsed_frame.rowconfigure(0, weight=1)
        
        self.parsed_text = scrolledtext.ScrolledText(parsed_frame, height=20, font=("Courier", 10))
        self.parsed_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 4. 統計資訊
        stats_frame = ttk.LabelFrame(main_frame, text="統計資訊", padding="5")
        stats_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="總字節: 0 | 數據幀: 0 | 命令幀: 0")
        self.stats_label.grid(row=0, column=0, sticky=tk.W)
        
        # 控制按鈕
        btn_frame = ttk.Frame(stats_frame)
        btn_frame.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Button(btn_frame, text="清除顯示", command=self.clear_display).grid(row=0, column=0, padx=(0, 5))
        self.monitor_btn = ttk.Button(btn_frame, text="開始監控", command=self.toggle_monitoring)
        self.monitor_btn.grid(row=0, column=1)
        
    def toggle_connection(self):
        if not self.is_connected:
            try:
                self.port_name = self.port_var.get()
                self.baud_rate = int(self.baud_var.get())
                self.log_message(f"正在連接到 {self.port_name}，波特率 {self.baud_rate}...")
                
                self.serial_port = serial.Serial(self.port_name, self.baud_rate, timeout=1)
                self.is_connected = True
                self.connect_btn.config(text="斷開")
                self.status_label.config(text="已連接", foreground="green")
                
                self.log_message(f"✅ 成功連接到 {self.port_name}")
                self.log_message("提示：點擊「開始監控」來接收數據")
                self.log_raw_data(f"連接成功 - {self.port_name} @ {self.baud_rate} bps")
                
            except Exception as e:
                error_msg = f"無法連接到串列埠: {str(e)}"
                self.log_message(f"❌ {error_msg}")
                messagebox.showerror("連接錯誤", error_msg)
        else:
            if self.serial_port:
                self.serial_port.close()
            self.is_connected = False
            self.is_monitoring = False
            self.connect_btn.config(text="連接")
            self.monitor_btn.config(text="開始監控")
            self.status_label.config(text="未連接", foreground="red")
            self.log_message("已斷開連接")
            self.log_raw_data("連接已斷開")
    
    def toggle_monitoring(self):
        if not self.is_connected:
            messagebox.showwarning("警告", "請先連接串列埠")
            self.log_message("⚠️  請先連接串列埠再開始監控")
            return
            
        self.is_monitoring = not self.is_monitoring
        if self.is_monitoring:
            self.monitor_btn.config(text="停止監控")
            self.log_message("🔍 開始監控數據...")
            self.log_message("提示：如果沒有數據，請發送「開始數據輸出」命令")
            self.log_raw_data("開始監控 - 等待數據...")
        else:
            self.monitor_btn.config(text="開始監控")
            self.log_message("⏹️  停止監控")
            self.log_raw_data("監控已停止")
    
    def send_predefined_command(self):
        if not self.is_connected:
            messagebox.showwarning("警告", "請先連接串列埠")
            self.log_message("⚠️  請先連接串列埠再發送命令")
            return
            
        cmd_name = self.cmd_var.get()
        if cmd_name in self.predefined_commands:
            hex_cmd = self.predefined_commands[cmd_name]
            self.send_hex_command(hex_cmd, cmd_name)
        else:
            self.log_message("⚠️  請選擇一個預定義命令")
    
    def send_custom_command(self):
        if not self.is_connected:
            messagebox.showwarning("警告", "請先連接串列埠")
            self.log_message("⚠️  請先連接串列埠再發送命令")
            return
            
        hex_cmd = self.custom_cmd_var.get().strip()
        if hex_cmd:
            self.send_hex_command(hex_cmd, "自定義命令")
        else:
            self.log_message("⚠️  請輸入自定義命令")
    
    def send_hex_command(self, hex_string, cmd_name):
        try:
            # 解析16進制字串
            hex_bytes = bytes.fromhex(hex_string.replace(" ", ""))
            
            # 發送命令
            self.serial_port.write(hex_bytes)
            self.serial_port.flush()
            
            # 記錄
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_message(f"📤 [{timestamp}] 發送 {cmd_name}")
            self.log_raw_data(f">>> 發送 {cmd_name}: {hex_string}")
            self.log_parsed_data(f"[{timestamp}] 命令已發送: {cmd_name}\n16進制: {hex_string}\n")
            
            # 如果是開始數據輸出命令，提醒用戶
            if "12 00" in hex_string:
                self.log_message("💡 已發送數據輸出命令，應該很快會看到數據")
                
        except Exception as e:
            error_msg = f"發送命令失敗: {str(e)}"
            self.log_message(f"❌ {error_msg}")
            messagebox.showerror("發送錯誤", error_msg)
    
    def start_data_thread(self):
        self.data_thread = threading.Thread(target=self.data_reader, daemon=True)
        self.data_thread.start()
        
        # 啟動UI更新
        self.root.after(100, self.update_ui)
    
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
                    self.log_message(f"讀取錯誤: {data}")
            except queue.Empty:
                break
        
        # 更新統計
        self.update_stats()
        
        # 繼續更新
        self.root.after(100, self.update_ui)
    
    def process_received_data(self, data):
        self.raw_buffer.extend(data)
        self.stats['total_bytes'] += len(data)
        
        # 顯示原始數據
        hex_data = ' '.join(f'{b:02X}' for b in data)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_raw_data(f"[{timestamp}] 接收: {hex_data}")
        
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
                    self.parse_data_frame(frame)
                    self.stats['data_frames'] += 1
                    i = end_pos
                else:
                    i += 1
            
            # 查找命令幀 FD FC FB FA ... 04 03 02 01
            elif (buffer[i:i+4] == b'\xFD\xFC\xFB\xFA'):
                end_pos = -1
                for j in range(i + 8, len(buffer) - 3):
                    if buffer[j:j+4] == b'\x04\x03\x02\x01':
                        end_pos = j + 4
                        break
                
                if end_pos != -1:
                    frame = buffer[i:end_pos]
                    self.parse_cmd_frame(frame)
                    self.stats['cmd_frames'] += 1
                    i = end_pos
                else:
                    i += 1
            else:
                i += 1
        
        # 清理已處理的數據
        if len(self.raw_buffer) > 1000:
            self.raw_buffer = self.raw_buffer[-500:]
    
    def parse_data_frame(self, frame):
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = f"\n[{timestamp}] === 數據幀分析 ===\n"
        result += f"長度: {len(frame)} 字節\n"
        result += f"完整幀: {' '.join(f'{b:02X}' for b in frame)}\n"
        
        if len(frame) >= 23:
            # 解析數據
            target_state = frame[8]
            move_dist = (frame[10] << 8) | frame[9]
            move_energy = frame[11]
            still_dist = (frame[13] << 8) | frame[12]
            still_energy = frame[14]
            detect_dist = (frame[16] << 8) | frame[15]
            
            result += f"目標狀態: 0x{target_state:02X} ("
            if target_state & 0x01: result += "目標存在 "
            if target_state & 0x02: result += "移動目標 "
            if target_state & 0x04: result += "靜止目標 "
            result += ")\n"
            
            result += f"移動目標: {move_dist}cm, 能量:{move_energy}\n"
            result += f"靜止目標: {still_dist}cm, 能量:{still_energy}\n"
            result += f"檢測距離: {detect_dist}cm\n"
            
            if len(frame) > 45:
                light_sensor = frame[45]
                result += f"光感數據: {light_sensor}\n"
        
        self.log_parsed_data(result)
    
    def parse_cmd_frame(self, frame):
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = f"\n[{timestamp}] === 命令幀分析 ===\n"
        result += f"長度: {len(frame)} 字節\n"
        result += f"完整幀: {' '.join(f'{b:02X}' for b in frame)}\n"
        
        if len(frame) >= 7:
            cmd_code = frame[6]
            result += f"命令碼: 0x{cmd_code:02X} ("
            
            cmd_names = {
                0xFF: "進入配置模式",
                0xFE: "退出配置模式", 
                0xA0: "查詢版本",
                0x12: "查詢數據",
                0x60: "設定距離",
                0x64: "設定門檻",
                0xA2: "恢復出廠設定",
                0xA3: "重啟模組"
            }
            
            result += cmd_names.get(cmd_code, "未知命令") + ")\n"
            
            if len(frame) > 8:
                result += f"命令數據: {' '.join(f'{b:02X}' for b in frame[8:-4])}\n"
        
        self.log_parsed_data(result)
    
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_parsed_data(f"[{timestamp}] {message}\n")
    
    def log_raw_data(self, data):
        self.raw_text.insert(tk.END, data + "\n")
        self.raw_text.see(tk.END)
    
    def log_parsed_data(self, data):
        self.parsed_text.insert(tk.END, data + "\n")
        self.parsed_text.see(tk.END)
    
    def update_stats(self):
        stats_text = f"總字節: {self.stats['total_bytes']} | 數據幀: {self.stats['data_frames']} | 命令幀: {self.stats['cmd_frames']}"
        self.stats_label.config(text=stats_text)
    
    def clear_display(self):
        self.raw_text.delete(1.0, tk.END)
        self.parsed_text.delete(1.0, tk.END)
        self.stats = {'total_bytes': 0, 'data_frames': 0, 'cmd_frames': 0}
        self.raw_buffer.clear()

    def show_welcome_message(self):
        welcome_msg = """
=== LD2412 雷達傳感器圖形化控制介面 ===
版本: v2.0
功能: 16進制數據分析 + 命令控制

使用步驟:
1. 確認串列埠路徑正確
2. 點擊「連接」按鈕連接設備
3. 點擊「開始監控」開始接收數據
4. 使用預定義命令或自定義命令與LD2412互動

當前設定:
- 串列埠: /dev/cu.usbserial-0001
- 波特率: 115200
- 狀態: 未連接

提示: 如果看不到數據，請先發送「開始數據輸出」命令
        """
        
        self.log_parsed_data(welcome_msg)
        self.log_raw_data("程序已啟動，等待連接...")
        
        # 檢查串列埠是否存在
        try:
            import os
            if os.path.exists(self.port_name):
                self.log_message(f"✅ 串列埠 {self.port_name} 存在")
            else:
                self.log_message(f"⚠️  串列埠 {self.port_name} 不存在，請檢查設備連接")
                # 列出可用的串列埠
                available_ports = []
                for port in ["/dev/cu.usbserial-0001", "/dev/cu.usbserial-1410", "/dev/cu.wchusbserial1410"]:
                    if os.path.exists(port):
                        available_ports.append(port)
                
                if available_ports:
                    self.log_message(f"可用串列埠: {', '.join(available_ports)}")
                else:
                    self.log_message("未找到USB串列埠，請檢查設備連接")
        except Exception as e:
            self.log_message(f"檢查串列埠時出錯: {e}")
        
        self.log_message("程序初始化完成！")

def main():
    root = tk.Tk()
    app = LD2412GUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 