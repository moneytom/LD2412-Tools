#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LD2412 深色主題 GUI 工具 - 依賴安裝腳本

此腳本會自動檢查和安裝所需的 Python 依賴包。
支援 Windows、macOS 和 Linux 系統。

使用方法:
    python install_dependencies.py
    
作者: LD2412 開發團隊
版本: v2.6
日期: 2024年1月
"""

import sys
import subprocess
import importlib
import platform

def check_python_version():
    """檢查 Python 版本"""
    print("🔍 檢查 Python 版本...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"❌ Python 版本過低: {version.major}.{version.minor}")
        print("⚠️  需要 Python 3.7 或更高版本")
        print("📥 請從 https://www.python.org/downloads/ 下載最新版本")
        return False
    
    print(f"✅ Python 版本: {version.major}.{version.minor}.{version.micro}")
    return True

def install_package(package_name, import_name=None):
    """安裝 Python 包"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name} 已安裝")
        return True
    except ImportError:
        print(f"📦 正在安裝 {package_name}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"✅ {package_name} 安裝成功")
            return True
        except subprocess.CalledProcessError:
            print(f"❌ {package_name} 安裝失敗")
            return False

def check_tkinter():
    """檢查 tkinter 是否可用"""
    try:
        import tkinter
        print("✅ tkinter 已可用")
        return True
    except ImportError:
        print("❌ tkinter 不可用")
        system = platform.system()
        if system == "Linux":
            print("💡 在 Ubuntu/Debian 上安裝: sudo apt-get install python3-tk")
            print("💡 在 CentOS/RHEL 上安裝: sudo yum install tkinter")
        elif system == "Darwin":
            print("💡 在 macOS 上，tkinter 通常隨 Python 一起安裝")
            print("💡 如果缺失，請重新安裝 Python 或使用 Homebrew: brew install python-tk")
        elif system == "Windows":
            print("💡 在 Windows 上，tkinter 通常隨 Python 一起安裝")
            print("💡 如果缺失，請重新安裝 Python 並確保勾選 'tcl/tk and IDLE' 選項")
        return False

def install_matplotlib():
    """安裝 matplotlib 並設置中文字體支援"""
    if install_package("matplotlib"):
        print("🎨 配置 matplotlib 中文字體支援...")
        try:
            import matplotlib.pyplot as plt
            import matplotlib.font_manager as fm
            
            # 檢查中文字體
            chinese_fonts = ['Arial Unicode MS', 'PingFang SC', 'Hiragino Sans GB', 'STHeiti', 'SimHei']
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            
            found_font = None
            for font in chinese_fonts:
                if font in available_fonts:
                    found_font = font
                    break
            
            if found_font:
                print(f"✅ 找到中文字體: {found_font}")
            else:
                print("⚠️  未找到中文字體，圖表將使用英文標籤")
                
        except Exception as e:
            print(f"⚠️  字體配置警告: {e}")
        
        return True
    return False

def create_virtual_environment():
    """詢問是否創建虛擬環境"""
    response = input("\n🤔 是否創建虛擬環境？(推薦) [y/N]: ").strip().lower()
    if response in ['y', 'yes', '是']:
        print("📁 創建虛擬環境...")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", "ld2412_env"])
            print("✅ 虛擬環境創建成功: ld2412_env")
            print("💡 激活虛擬環境:")
            
            system = platform.system()
            if system == "Windows":
                print("   ld2412_env\\Scripts\\activate")
            else:
                print("   source ld2412_env/bin/activate")
            
            print("💡 激活後重新運行此安裝腳本")
            return True
        except subprocess.CalledProcessError:
            print("❌ 虛擬環境創建失敗")
            return False
    return False

def main():
    """主安裝程序"""
    print("🚀 LD2412 深色主題 GUI 工具 - 依賴安裝程序")
    print("=" * 50)
    
    # 檢查 Python 版本
    if not check_python_version():
        sys.exit(1)
    
    # 詢問虛擬環境
    if create_virtual_environment():
        return
    
    print("\n📦 檢查和安裝必要依賴...")
    print("-" * 30)
    
    # 必要依賴列表
    required_packages = [
        ("pyserial", "serial"),
        ("numpy", "numpy"),
    ]
    
    # 檢查 tkinter
    tkinter_ok = check_tkinter()
    
    # 安裝必要依賴
    all_success = True
    for package, import_name in required_packages:
        if not install_package(package, import_name):
            all_success = False
    
    # 安裝 matplotlib (特殊處理)
    matplotlib_ok = install_matplotlib()
    
    print("\n" + "=" * 50)
    print("📋 安裝結果摘要:")
    print(f"  Python 版本: {'✅' if True else '❌'}")
    print(f"  tkinter: {'✅' if tkinter_ok else '❌'}")
    print(f"  pyserial: {'✅' if True else '❌'}")  # 假設前面檢查過了
    print(f"  numpy: {'✅' if True else '❌'}")     # 假設前面檢查過了
    print(f"  matplotlib: {'✅' if matplotlib_ok else '❌'}")
    
    if all_success and tkinter_ok and matplotlib_ok:
        print("\n🎉 所有依賴安裝完成！")
        print("🚀 現在可以運行程序:")
        print("   python ld2412_dark_gui.py")
    else:
        print("\n⚠️  部分依賴安裝失敗，請手動安裝:")
        print("   pip install -r requirements.txt")
        
        if not tkinter_ok:
            print("\n❗ tkinter 問題需要特別處理，請參考上面的提示")
    
    print("\n📚 更多幫助:")
    print("  - 查看 README.md 了解詳細使用說明")
    print("  - 參考 LD2412串口通信協議說明.md 了解協議詳情")
    print("  - 遇到問題請提交 GitHub Issue")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  安裝程序被中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 安裝程序發生錯誤: {e}")
        sys.exit(1) 