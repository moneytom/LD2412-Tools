#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import serial.tools.list_ports
import os
import sys

def test_serial_connection():
    """測試串列埠連接"""
    print("=== LD2412 串列埠連接診斷工具 ===\n")
    
    # 1. 檢查可用串列埠
    print("🔍 掃描可用串列埠...")
    try:
        ports = list(serial.tools.list_ports.comports())
        if ports:
            print("✅ 找到以下串列埠:")
            for i, (port, desc, hwid) in enumerate(ports, 1):
                print(f"  {i}. {port} - {desc}")
                print(f"     硬體ID: {hwid}")
        else:
            print("❌ 未找到任何串列埠設備")
            return
    except Exception as e:
        print(f"❌ 掃描串列埠失敗: {e}")
        return
    
    # 2. 測試特定串列埠
    target_port = "/dev/tty.usbserial-0001"
    print(f"\n🔧 測試目標串列埠: {target_port}")
    
    # 檢查文件是否存在
    if not os.path.exists(target_port):
        print(f"❌ 串列埠文件不存在: {target_port}")
        
        # 尋找類似的串列埠
        import glob
        similar_ports = glob.glob("/dev/tty.usbserial*") + glob.glob("/dev/cu.usbserial*")
        if similar_ports:
            print("💡 找到類似的串列埠:")
            for port in similar_ports:
                print(f"  • {port}")
        return
    
    print(f"✅ 串列埠文件存在: {target_port}")
    
    # 檢查權限
    try:
        stat_info = os.stat(target_port)
        print(f"📋 文件權限: {oct(stat_info.st_mode)[-3:]}")
        
        # 檢查是否可讀寫
        readable = os.access(target_port, os.R_OK)
        writable = os.access(target_port, os.W_OK)
        print(f"📖 可讀: {'✅' if readable else '❌'}")
        print(f"📝 可寫: {'✅' if writable else '❌'}")
        
        if not (readable and writable):
            print(f"💡 建議執行: sudo chmod 666 {target_port}")
            
    except Exception as e:
        print(f"❌ 檢查權限失敗: {e}")
    
    # 3. 嘗試開啟串列埠
    print(f"\n🔌 嘗試開啟串列埠...")
    baud_rates = [115200, 256000, 9600]
    
    for baud_rate in baud_rates:
        try:
            print(f"  測試波特率: {baud_rate}")
            ser = serial.Serial(
                port=target_port,
                baudrate=baud_rate,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            if ser.is_open:
                print(f"  ✅ 成功開啟 (波特率: {baud_rate})")
                
                # 測試讀寫
                try:
                    ser.reset_input_buffer()
                    ser.reset_output_buffer()
                    print(f"  ✅ 緩衝區清空成功")
                    
                    # 嘗試讀取一些數據（非阻塞）
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting)
                        print(f"  📥 接收到 {len(data)} 字節數據")
                    else:
                        print(f"  📭 暫無數據")
                        
                except Exception as e:
                    print(f"  ⚠️ 讀寫測試失敗: {e}")
                
                ser.close()
                print(f"  🔌 串列埠已關閉")
                break
            else:
                print(f"  ❌ 開啟失敗")
                
        except serial.SerialException as e:
            print(f"  ❌ 串列埠錯誤 (波特率 {baud_rate}): {e}")
        except Exception as e:
            print(f"  ❌ 未知錯誤 (波特率 {baud_rate}): {e}")
    
    print(f"\n✅ 診斷完成!")

if __name__ == "__main__":
    test_serial_connection() 