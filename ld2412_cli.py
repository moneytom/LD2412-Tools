#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import threading
import time
import queue
from datetime import datetime
import os

class LD2412CLI:
    def __init__(self):
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
            "1": ("進入配置模式", "FD FC FB FA 04 00 FF 00 01 00 04 03 02 01"),
            "2": ("退出配置模式", "FD FC FB FA 02 00 FE 00 04 03 02 01"),
            "3": ("查詢版本", "FD FC FB FA 02 00 A0 00 04 03 02 01"),
            "4": ("開始數據輸出", "FD FC FB FA 02 00 12 00 04 03 02 01"),
            "5": ("查詢參數", "FD FC FB FA 02 00 61 00 04 03 02 01"),
            "6": ("重啟模組", "FD FC FB FA 02 00 A3 00 04 03 02 01"),
            "7": ("恢復出廠設定", "FD FC FB FA 02 00 A2 00 04 03 02 01")
        }
        
        self.running = True
        self.start_data_thread()
        
    def start_data_thread(self):
        self.data_thread = threading.Thread(target=self.data_reader, daemon=True)
        self.data_thread.start()
        
    def data_reader(self):
        while self.running:
            if self.is_connected and self.serial_port and self.is_monitoring:
                try:
                    if self.serial_port.in_waiting:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        self.data_queue.put(('data', data))
                except Exception as e:
                    self.data_queue.put(('error', str(e)))
            time.sleep(0.01)
    
    def process_data_queue(self):
        while not self.data_queue.empty():
            try:
                msg_type, data = self.data_queue.get_nowait()
                if msg_type == 'data':
                    self.process_received_data(data)
                elif msg_type == 'error':
                    print(f"❌ 讀取錯誤: {data}")
            except queue.Empty:
                break
    
    def process_received_data(self, data):
        self.raw_buffer.extend(data)
        self.stats['total_bytes'] += len(data)
        
        # 顯示原始數據
        hex_data = ' '.join(f'{b:02X}' for b in data)
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"📥 [{timestamp}] 接收: {hex_data}")
        
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
        print(f"\n🔍 [{timestamp}] === 數據幀分析 ===")
        print(f"長度: {len(frame)} 字節")
        print(f"完整幀: {' '.join(f'{b:02X}' for b in frame)}")
        
        if len(frame) >= 23:
            # 解析數據
            target_state = frame[8]
            move_dist = (frame[10] << 8) | frame[9]
            move_energy = frame[11]
            still_dist = (frame[13] << 8) | frame[12]
            still_energy = frame[14]
            detect_dist = (frame[16] << 8) | frame[15]
            
            status_text = "目標狀態: 0x{:02X} (".format(target_state)
            if target_state & 0x01: status_text += "目標存在 "
            if target_state & 0x02: status_text += "移動目標 "
            if target_state & 0x04: status_text += "靜止目標 "
            status_text += ")"
            print(status_text)
            
            print(f"移動目標: {move_dist}cm, 能量:{move_energy}")
            print(f"靜止目標: {still_dist}cm, 能量:{still_energy}")
            print(f"檢測距離: {detect_dist}cm")
            
            if len(frame) > 45:
                light_sensor = frame[45]
                print(f"光感數據: {light_sensor}")
        
        print("=" * 50)
    
    def parse_cmd_frame(self, frame):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n📋 [{timestamp}] === 命令幀分析 ===")
        print(f"長度: {len(frame)} 字節")
        print(f"完整幀: {' '.join(f'{b:02X}' for b in frame)}")
        
        if len(frame) >= 7:
            cmd_code = frame[6]
            cmd_text = f"命令碼: 0x{cmd_code:02X} ("
            
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
            
            cmd_text += cmd_names.get(cmd_code, "未知命令") + ")"
            print(cmd_text)
            
            if len(frame) > 8:
                print(f"命令數據: {' '.join(f'{b:02X}' for b in frame[8:-4])}")
        
        print("=" * 50)
    
    def connect(self):
        if self.is_connected:
            print("⚠️  已經連接")
            return
        
        try:
            print(f"🔌 正在連接到 {self.port_name}，波特率 {self.baud_rate}...")
            self.serial_port = serial.Serial(self.port_name, self.baud_rate, timeout=1)
            self.is_connected = True
            print(f"✅ 成功連接到 {self.port_name}")
            print("💡 提示：使用 'm' 開始監控，使用命令編號發送指令")
        except Exception as e:
            print(f"❌ 連接失敗: {e}")
    
    def disconnect(self):
        if not self.is_connected:
            print("⚠️  尚未連接")
            return
        
        if self.serial_port:
            self.serial_port.close()
        self.is_connected = False
        self.is_monitoring = False
        print("🔌 已斷開連接")
    
    def toggle_monitoring(self):
        if not self.is_connected:
            print("⚠️  請先連接串列埠")
            return
        
        self.is_monitoring = not self.is_monitoring
        if self.is_monitoring:
            print("🔍 開始監控數據...")
            print("💡 如果沒有數據，請發送命令 4 (開始數據輸出)")
        else:
            print("⏹️  停止監控")
    
    def send_command(self, cmd_key):
        if not self.is_connected:
            print("⚠️  請先連接串列埠")
            return
        
        if cmd_key not in self.predefined_commands:
            print("⚠️  無效的命令編號")
            return
        
        cmd_name, hex_string = self.predefined_commands[cmd_key]
        
        try:
            hex_bytes = bytes.fromhex(hex_string.replace(" ", ""))
            self.serial_port.write(hex_bytes)
            self.serial_port.flush()
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"📤 [{timestamp}] 發送 {cmd_name}")
            print(f"   16進制: {hex_string}")
            
            if "12 00" in hex_string:
                print("💡 已發送數據輸出命令，應該很快會看到數據")
                
        except Exception as e:
            print(f"❌ 發送失敗: {e}")
    
    def send_custom_command(self, hex_string):
        if not self.is_connected:
            print("⚠️  請先連接串列埠")
            return
        
        try:
            hex_bytes = bytes.fromhex(hex_string.replace(" ", ""))
            self.serial_port.write(hex_bytes)
            self.serial_port.flush()
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"📤 [{timestamp}] 發送自定義命令")
            print(f"   16進制: {hex_string}")
            
        except Exception as e:
            print(f"❌ 發送失敗: {e}")
    
    def show_stats(self):
        print(f"\n📊 統計資訊:")
        print(f"總字節: {self.stats['total_bytes']}")
        print(f"數據幀: {self.stats['data_frames']}")
        print(f"命令幀: {self.stats['cmd_frames']}")
        print(f"連接狀態: {'已連接' if self.is_connected else '未連接'}")
        print(f"監控狀態: {'監控中' if self.is_monitoring else '已停止'}")
    
    def show_help(self):
        print("""
🎯 LD2412 命令行控制介面

📋 基本命令:
  c  - 連接串列埠
  d  - 斷開連接
  m  - 開始/停止監控
  s  - 顯示統計資訊
  h  - 顯示此幫助
  q  - 退出程序

📤 預定義命令:""")
        
        for key, (name, _) in self.predefined_commands.items():
            print(f"  {key}  - {name}")
        
        print("""
🔧 自定義命令:
  x <16進制>  - 發送自定義命令
  例如: x FD FC FB FA 02 00 A0 00 04 03 02 01

💡 使用提示:
  1. 先使用 'c' 連接設備
  2. 使用 'm' 開始監控
  3. 使用 '4' 發送開始數據輸出命令
  4. 觀察數據分析結果
        """)
    
    def check_serial_ports(self):
        print("🔍 檢查串列埠:")
        test_ports = ["/dev/cu.usbserial-0001", "/dev/cu.usbserial-1410", "/dev/cu.wchusbserial1410"]
        
        for port in test_ports:
            if os.path.exists(port):
                print(f"  ✅ {port} - 存在")
            else:
                print(f"  ❌ {port} - 不存在")
    
    def run(self):
        print("=" * 60)
        print("🎯 LD2412 雷達傳感器命令行控制介面 v2.0")
        print("=" * 60)
        
        self.check_serial_ports()
        self.show_help()
        
        while self.running:
            try:
                # 處理接收到的數據
                self.process_data_queue()
                
                # 獲取用戶輸入
                try:
                    cmd = input("\n>>> ").strip().lower()
                except KeyboardInterrupt:
                    print("\n👋 程序中斷")
                    break
                
                if cmd == 'q':
                    break
                elif cmd == 'c':
                    self.connect()
                elif cmd == 'd':
                    self.disconnect()
                elif cmd == 'm':
                    self.toggle_monitoring()
                elif cmd == 's':
                    self.show_stats()
                elif cmd == 'h':
                    self.show_help()
                elif cmd in self.predefined_commands:
                    self.send_command(cmd)
                elif cmd.startswith('x '):
                    hex_cmd = cmd[2:].strip()
                    if hex_cmd:
                        self.send_custom_command(hex_cmd)
                    else:
                        print("⚠️  請輸入16進制命令")
                elif cmd:
                    print("⚠️  無效命令，使用 'h' 查看幫助")
                    
            except Exception as e:
                print(f"❌ 錯誤: {e}")
        
        print("👋 程序結束")
        self.running = False
        if self.is_connected:
            self.disconnect()

def main():
    cli = LD2412CLI()
    cli.run()

if __name__ == "__main__":
    main() 