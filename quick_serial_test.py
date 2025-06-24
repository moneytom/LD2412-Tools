#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速串列埠測試腳本
用於驗證 LD2412 GUI 的串列埠連接問題
"""

def test_serial_import():
    """測試 serial 模組導入"""
    print("=== 測試 PySerial 模組導入 ===")
    try:
        import serial
        from serial import Serial, SerialException
        print("✅ PySerial 導入成功")
        print(f"Serial 類: {Serial}")
        print(f"SerialException 類: {SerialException}")
        return True
    except ImportError as e:
        print(f"❌ PySerial 導入失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知錯誤: {e}")
        return False

def test_port_connection():
    """測試串列埠連接"""
    print("\n=== 測試串列埠連接 ===")
    
    # 測試目標埠
    test_ports = [
        "/dev/cu.usbserial-0001",
        "/dev/tty.usbserial-0001"
    ]
    
    try:
        from serial import Serial, SerialException
        
        for port in test_ports:
            print(f"\n🔧 測試埠: {port}")
            
            # 檢查埠是否存在
            import os
            if not os.path.exists(port):
                print(f"❌ 埠不存在: {port}")
                continue
            
            try:
                # 嘗試連接
                ser = Serial(
                    port=port,
                    baudrate=115200,
                    timeout=1
                )
                
                if ser.is_open:
                    print(f"✅ 成功連接: {port}")
                    print(f"   波特率: {ser.baudrate}")
                    print(f"   超時時間: {ser.timeout}")
                    
                    # 測試基本操作
                    ser.reset_input_buffer()
                    ser.reset_output_buffer()
                    print("✅ 緩衝區重置成功")
                    
                    ser.close()
                    print("✅ 連接已關閉")
                    return True
                else:
                    print(f"❌ 連接失敗: 埠未開啟")
                    
            except SerialException as e:
                print(f"❌ 串列埠錯誤: {e}")
                
            except Exception as e:
                print(f"❌ 未知錯誤: {e}")
                
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False
    
    return False

def main():
    """主函數"""
    print("🚀 LD2412 串列埠快速測試")
    print("=" * 50)
    
    # 測試導入
    if not test_serial_import():
        print("\n❌ PySerial 模組有問題，請安裝: pip install pyserial")
        return
    
    # 測試連接
    if test_port_connection():
        print("\n✅ 串列埠測試通過！GUI 應該能正常連接")
    else:
        print("\n❌ 串列埠測試失敗，請檢查:")
        print("   1. 設備是否正確連接")
        print("   2. USB 線是否為數據線")
        print("   3. 驅動程序是否正確安裝")
        print("   4. 埠權限是否正確")

if __name__ == "__main__":
    main() 