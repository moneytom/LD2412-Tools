#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import queue
from datetime import datetime
from collections import deque
import os

# 明確導入 serial 模組以避免命名衝突
try:
    import serial
    from serial import Serial, SerialException
    print("✅ PySerial 已成功導入")
except ImportError as e:
    print(f"❌ PySerial 導入失敗: {e}")
    print("請安裝 pyserial: pip install pyserial")
    serial = None

# 圖表相關套件 - 可選導入
try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import numpy as np
    
    # 設置matplotlib為深色主題
    plt.style.use('dark_background')
    
    # 設置中文字體支援（macOS）
    try:
        import matplotlib.font_manager as fm
        # 嘗試設置中文字體
        chinese_fonts = ['Arial Unicode MS', 'PingFang SC', 'Hiragino Sans GB', 'STHeiti', 'SimHei']
        for font in chinese_fonts:
            if font in [f.name for f in fm.fontManager.ttflist]:
                plt.rcParams['font.sans-serif'] = [font, 'DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
                print(f"✅ 已設置中文字體: {font}")
                break
        else:
            # 如果沒有中文字體，使用英文標籤
            print("⚠️ 未找到中文字體，將使用英文標籤")
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    except Exception as e:
        print(f"⚠️ 字體設置失敗: {e}")
    
    MATPLOTLIB_AVAILABLE = True
    print("✅ matplotlib 已載入，圖表功能可用")
except ImportError as e:
    print(f"⚠️ matplotlib 未安裝或載入失敗: {e}")
    print("📝 將使用文字版圖表，如需圖表功能請執行: pip install matplotlib numpy")
    MATPLOTLIB_AVAILABLE = False

# 消除macOS上的tkinter警告
os.environ['TK_SILENCE_DEPRECATION'] = '1'

class DarkLD2412GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LD2412 雷達數據分析系統 (深色版)")
        self.root.geometry("1400x900")  # 調整為更合適的分頁界面大小
        
        # 深色主題配色
        self.colors = {
            'bg_dark': '#2b2b2b',           # 深色背景
            'bg_medium': '#3c3c3c',         # 中等背景
            'bg_light': '#4a4a4a',          # 淺色背景
            'fg_primary': '#ffffff',        # 主要文字
            'fg_secondary': '#cccccc',      # 次要文字
            'accent_blue': '#4a9eff',       # 藍色強調
            'accent_green': '#4ade80',      # 綠色強調
            'accent_red': '#ef4444',        # 紅色強調
            'accent_yellow': '#fbbf24',     # 黃色強調
            'border': '#555555'             # 邊框顏色
        }
        
        # 設置深色主題
        self.setup_dark_theme()
        
        # 串列埠設定
        self.port_name = "/dev/cu.usbserial-0001"
        self.baud_rate = 115200
        self.serial_port = None
        self.is_connected = False
        self.is_monitoring = False
        
        # 配置模式狀態追蹤
        self.is_config_mode = False
        self.last_command_time = 0
        
        # 命令回應追蹤
        self.waiting_for_response = False
        self.last_command_sent = ""
        self.command_timeout = 1.0  # 命令超時時間
        
        # 數據處理
        self.data_queue = queue.Queue()
        self.raw_buffer = bytearray()
        
        # 新增：定時分析機制
        self.last_analysis_time = 0
        self.analysis_interval = 0.1  # 每0.1秒分析一次
        
        # 數據歷史
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
            'start_time': time.time(),
            'max_distance': 0,
            'min_distance': 9999,
            'last_update': time.time()
        }
        
        # 當前數據
        self.current_data = None
        
        # 敏感度閾值（會根據查詢結果自動更新）
        self.moving_sensitivity_threshold = 50  # 預設值（用於顯示平均參考線）
        self.still_sensitivity_threshold = 25   # 預設值（用於顯示平均參考線）
        
        # 每個門的敏感度設定（14個門）
        self.moving_gate_sensitivities = [50] * 14  # 預設值
        self.still_gate_sensitivities = [25] * 14   # 預設值
        
        self.create_widgets()
        self.start_data_thread()
        self.update_display()
        
        # 初始化
        self.log("🚀 LD2412深色主題GUI已啟動")
        self.log("✅ 狀態位解析已根據協議文檔修正 (v2.6)")
        self.log("📊 支援狀態: 無目標(0x00), 運動(0x01), 靜止(0x02), 運動&靜止(0x03), 底噪檢測(0x04-0x06)")
        self.log("🧪 可使用「狀態解析測試」功能驗證解析正確性")
        self.log("⚙️ 配置功能已移至「配置管理」分頁，主控制面板更簡潔")
        self.log("🎯 雷達圖圖例位置已優化，敏感度更新機制已修復")
        
    def setup_dark_theme(self):
        """設置深色主題"""
        self.root.configure(bg=self.colors['bg_dark'])
        
        # 配置ttk樣式 - 簡化版本
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置基本樣式，不使用自定義名稱
        style.configure('TFrame', 
                       background=self.colors['bg_dark'],
                       borderwidth=1)
        
        style.configure('TLabelFrame', 
                       background=self.colors['bg_dark'],
                       foreground=self.colors['fg_primary'],
                       borderwidth=2)
        
        style.configure('TLabel', 
                       background=self.colors['bg_dark'],
                       foreground=self.colors['fg_primary'])
        
        style.configure('TButton', 
                       background=self.colors['bg_medium'],
                       foreground=self.colors['fg_primary'],
                       borderwidth=1,
                       focuscolor='none')
        
        style.map('TButton',
                 background=[('active', self.colors['accent_blue']),
                           ('pressed', self.colors['bg_light'])])
        
        style.configure('TEntry', 
                       fieldbackground=self.colors['bg_medium'],
                       foreground=self.colors['fg_primary'],
                       borderwidth=1)
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. 控制區域 - 固定在頂部
        self.create_control_panel(main_frame)
        
        # 2. 日誌區域 - 固定在控制面板下方
        log_frame = ttk.LabelFrame(main_frame, text="📝 系統日誌與警報", padding="5")
        log_frame.pack(fill=tk.X, pady=(10, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=4, font=("Courier", 12),
                                                bg=self.colors['bg_medium'], 
                                                fg=self.colors['fg_secondary'],
                                                insertbackground=self.colors['fg_primary'],
                                                wrap=tk.WORD)
        self.log_text.pack(fill=tk.X)
        
        # 3. 分頁控件
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 創建各個分頁
        self.create_realtime_tab()
        self.create_data_analysis_tab()
        self.create_chart_tab()
        self.create_config_tab()  # 新增配置分頁
        self.create_raw_data_tab()
        self.create_detailed_analysis_tab()  # 新增詳細解析分頁
        
    def create_control_panel(self, parent):
        control_frame = ttk.LabelFrame(parent, text="🎛️ 控制面板", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 連接控制
        conn_frame = ttk.Frame(control_frame)
        conn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(conn_frame, text="串列埠:").pack(side=tk.LEFT, padx=5)
        self.port_var = tk.StringVar(value=self.port_name)
        
        # 創建串列埠下拉選單
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, width=25)
        self.port_combo.pack(side=tk.LEFT, padx=5)
        
        # 初始化串列埠列表
        self.update_port_list()
        
        # 增加波特率選擇
        ttk.Label(conn_frame, text="波特率:").pack(side=tk.LEFT, padx=(20, 5))
        self.baud_var = tk.StringVar(value="115200")  # 根據協議文檔，預設為256000
        baud_combo = ttk.Combobox(conn_frame, textvariable=self.baud_var, width=10,
                                 values=["256000", "460800", "230400", "115200", "57600", "38400", "19200", "9600"],  # 按協議文檔順序排列
                                 state="readonly")
        baud_combo.pack(side=tk.LEFT, padx=5)
        baud_combo.current(3)  # 預設選擇115200
        
        self.connect_btn = ttk.Button(conn_frame, text="🔌 連接", command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.monitor_btn = ttk.Button(conn_frame, text="▶️ 開始監控", command=self.toggle_monitoring)
        self.monitor_btn.pack(side=tk.LEFT, padx=5)
        
        # 刷新串列埠按鈕
        refresh_btn = ttk.Button(conn_frame, text="🔍 掃描埠", command=self.refresh_ports)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # 快速操作按鈕
        self.quick_start_btn = ttk.Button(conn_frame, text="⚡ 快速開始", command=self.quick_start)
        self.quick_start_btn.pack(side=tk.LEFT, padx=5)
        
        # 狀態標籤 - 使用tk.Label而不是ttk.Label以便自定義顏色
        self.status_label = tk.Label(conn_frame, text="🔴 未連接", 
                                   bg=self.colors['bg_dark'], 
                                   fg=self.colors['accent_red'],
                                   font=('Arial', 12, 'bold'))
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # 配置模式指示器
        self.config_label = tk.Label(conn_frame, text="📝 正常模式", 
                                    bg=self.colors['bg_dark'], 
                                    fg=self.colors['fg_secondary'],
                                    font=('Arial', 10))
        self.config_label.pack(side=tk.LEFT, padx=10)
        
        # 即時狀態
        status_frame = ttk.Frame(conn_frame)
        status_frame.pack(side=tk.RIGHT, padx=20)
        
        self.frame_count_label = ttk.Label(status_frame, text="數據幀: 0")
        self.frame_count_label.pack(side=tk.LEFT, padx=10)
        
        self.fps_label = ttk.Label(status_frame, text="幀率: 0.0/s")
        self.fps_label.pack(side=tk.LEFT, padx=10)
        
        # 命令按鈕區域
        cmd_frame = ttk.LabelFrame(control_frame, text="📤 命令控制", padding="5")
        cmd_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 預定義命令按鈕 - 只保留最常用的基本操作
        commands = [
            # 基本數據控制
            ("📊 查詢參數", "FD FC FB FA 02 00 12 00 04 03 02 01"),      # CMD_QUERY (0x0012)
            ("📋 查詢版本", "FD FC FB FA 02 00 A0 00 04 03 02 01"),     # CMD_VERSION (0x00A0)
            ("🔄 重啟模組", "FD FC FB FA 02 00 A3 00 04 03 02 01"),     # CMD_RESTART (0x00A3)
            
            # 配置模式控制
            ("⚙️ 進入配置模式", "FD FC FB FA 04 00 FF 00 01 00 04 03 02 01"),  # CMD_ENABLE_CONF (0x00FF)
            ("🚪 退出配置模式", "FD FC FB FA 02 00 FE 00 04 03 02 01"),        # CMD_DISABLE_CONF (0x00FE)
            
            # 工程模式控制
            ("🔧 開啟工程模式", "FD FC FB FA 02 00 62 00 04 03 02 01"),   # CMD_ENABLE_ENG (0x0062)
            ("🔧 關閉工程模式", "FD FC FB FA 02 00 63 00 04 03 02 01"),   # CMD_DISABLE_ENG (0x0063)
            
            # 門敏感度查詢（最常用）
            ("📊 查詢移動門敏感度", "FD FC FB FA 02 00 13 00 04 03 02 01"),  # CMD_QUERY_MOTION_GATE_SENS (0x0013)
            ("📊 查詢靜止門敏感度", "FD FC FB FA 02 00 14 00 04 03 02 01"),  # CMD_QUERY_STATIC_GATE_SENS (0x0014)
            
            # 實用功能
            ("🗑️ 清除數據", None)
        ]
        
        # 創建按鈕網格 - 改為5列布局，更緊湊
        for i, (name, cmd) in enumerate(commands):
            if cmd:
                btn = ttk.Button(cmd_frame, text=name, command=lambda c=cmd: self.send_command(c), width=20)
            else:
                btn = ttk.Button(cmd_frame, text=name, command=self.clear_data, width=20)
            btn.grid(row=i//5, column=i%5, padx=2, pady=2, sticky=(tk.W, tk.E))
        
        # 配置列寬度
        for i in range(5):
            cmd_frame.columnconfigure(i, weight=1)
        
        # 常用功能組合按鈕區域 - 精簡版
        combo_frame = ttk.LabelFrame(cmd_frame, text="🎯 常用功能", padding="5")
        combo_frame.grid(row=3, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=(10, 5))
        
        combo_commands = [
            ("🔧 工程模式初始化", self.engineering_mode_init),
            ("📏 查詢所有設定", self.query_all_settings),
            ("🎯 標準配置", self.standard_config),
            ("🔄 完整重啟", self.full_restart)
        ]
        
        # 調整為4個按鈕的單行布局
        for i, (name, func) in enumerate(combo_commands):
            btn = ttk.Button(combo_frame, text=name, command=func, width=25)
            btn.grid(row=0, column=i, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # 配置組合按鈕的列寬度
        for i in range(4):
            combo_frame.columnconfigure(i, weight=1)
        
        # 自定義命令區域
        custom_frame = ttk.Frame(cmd_frame)
        custom_frame.grid(row=4, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(custom_frame, text="自定義命令:").pack(side=tk.LEFT, padx=5)
        self.custom_cmd_var = tk.StringVar()
        ttk.Entry(custom_frame, textvariable=self.custom_cmd_var, width=60).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(custom_frame, text="📤 發送", command=self.send_custom_command).pack(side=tk.LEFT, padx=5)
    
    def create_realtime_tab(self):
        """創建即時數據監控分頁"""
        realtime_tab = ttk.Frame(self.notebook)
        self.notebook.add(realtime_tab, text="📊 即時監控")
        
        # 即時數據顯示
        realtime_frame = ttk.LabelFrame(realtime_tab, text="即時數據分析", padding="10")
        realtime_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.realtime_text = tk.Text(realtime_frame, font=("Courier", 16),
                                   bg=self.colors['bg_medium'], fg=self.colors['fg_primary'],
                                   insertbackground=self.colors['fg_primary'])
        self.realtime_text.pack(fill=tk.BOTH, expand=True)
    
    def create_data_analysis_tab(self):
        """創建數據分析分頁"""
        analysis_tab = ttk.Frame(self.notebook)
        self.notebook.add(analysis_tab, text="📈 統計分析")
        
        # 統計分析顯示
        stats_frame = ttk.LabelFrame(analysis_tab, text="統計分析報告", padding="10")
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.stats_text = tk.Text(stats_frame, font=("Courier", 14),
                                bg=self.colors['bg_medium'], fg=self.colors['accent_blue'],
                                insertbackground=self.colors['fg_primary'])
        self.stats_text.pack(fill=tk.BOTH, expand=True)
    
    def create_chart_tab(self):
        """創建門能量分布圖分頁 - 根據matplotlib可用性選擇實現"""
        chart_tab = ttk.Frame(self.notebook)
        self.notebook.add(chart_tab, text="📊 門能量圖")
        
        if MATPLOTLIB_AVAILABLE:
            self.create_matplotlib_chart_tab(chart_tab)
        else:
            self.create_text_chart_tab(chart_tab)
    
    def create_matplotlib_chart_tab(self, parent):
        """創建matplotlib圖表分頁"""
        # 主容器 - 垂直分割
        main_container = ttk.Frame(parent)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 控制面板
        control_frame = ttk.LabelFrame(main_container, text="圖表控制", padding="5")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 圖表類型選擇
        ttk.Label(control_frame, text="圖表類型:").pack(side=tk.LEFT, padx=5)
        self.chart_type_var = tk.StringVar(value="bar")
        chart_type_combo = ttk.Combobox(control_frame, textvariable=self.chart_type_var, width=15,
                                       values=["bar", "line", "radar", "heatmap"], state="readonly")
        chart_type_combo.pack(side=tk.LEFT, padx=5)
        chart_type_combo.bind('<<ComboboxSelected>>', self.on_chart_type_change)
        
        # 更新間隔控制
        ttk.Label(control_frame, text="更新間隔:").pack(side=tk.LEFT, padx=(20, 5))
        self.update_interval_var = tk.StringVar(value="500")
        interval_combo = ttk.Combobox(control_frame, textvariable=self.update_interval_var, width=10,
                                     values=["100", "200", "500", "1000", "2000"], state="readonly")
        interval_combo.pack(side=tk.LEFT, padx=5)
        
        # 凍結/解凍按鈕
        self.freeze_btn = ttk.Button(control_frame, text="❄️ 凍結圖表", command=self.toggle_chart_freeze)
        self.freeze_btn.pack(side=tk.LEFT, padx=10)
        self.chart_frozen = False
        
        # 保存圖表按鈕
        save_btn = ttk.Button(control_frame, text="💾 保存圖表", command=self.save_chart)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # 圖表容器
        chart_container = ttk.Frame(main_container)
        chart_container.pack(fill=tk.BOTH, expand=True)
        
        # 創建matplotlib圖表
        self.setup_matplotlib_charts(chart_container)
        
        # 保留文字版本作為備份（隱藏）
        self.moving_chart_text = tk.Text(chart_container, font=("Courier", 8))
        self.still_chart_text = tk.Text(chart_container, font=("Courier", 8))
        self.chart_text = self.moving_chart_text  # 兼容性
    
    def create_text_chart_tab(self, parent):
        """創建文字版圖表分頁（matplotlib不可用時的備選方案）"""
        # 主容器 - 水平分割
        main_container = ttk.Frame(parent)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 提示信息
        info_frame = ttk.LabelFrame(main_container, text="📝 文字版圖表", padding="5")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_label = ttk.Label(info_frame, text="💡 如需專業圖表功能，請執行: pip install matplotlib numpy")
        info_label.pack(side=tk.LEFT, padx=5)
        
        # 移動目標能量圖（左側）
        moving_frame = ttk.LabelFrame(main_container, text="🏃 移動目標能量分布", padding="5")
        moving_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.moving_chart_text = tk.Text(moving_frame, font=("Courier", 11),
                                       bg=self.colors['bg_medium'], fg=self.colors['accent_blue'],
                                       insertbackground=self.colors['fg_primary'])
        self.moving_chart_text.pack(fill=tk.BOTH, expand=True)
        
        # 靜止目標能量圖（右側）
        still_frame = ttk.LabelFrame(main_container, text="🧍 靜止目標能量分布", padding="5")
        still_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.still_chart_text = tk.Text(still_frame, font=("Courier", 11),
                                      bg=self.colors['bg_medium'], fg=self.colors['accent_red'],
                                      insertbackground=self.colors['fg_primary'])
        self.still_chart_text.pack(fill=tk.BOTH, expand=True)
        
        # 保留原始的chart_text以兼容現有代碼
        self.chart_text = self.moving_chart_text
    
    def create_config_tab(self):
        """創建配置分頁 - 包含所有配置相關的功能"""
        config_tab = ttk.Frame(self.notebook)
        self.notebook.add(config_tab, text="⚙️ 配置管理")
        
        # 主容器
        main_container = ttk.Frame(config_tab)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 1. 距離分辨率配置區域
        resolution_frame = ttk.LabelFrame(main_container, text="🎯 距離分辨率設定", padding="10")
        resolution_frame.pack(fill=tk.X, pady=(0, 10))
        
        resolution_commands = [
            ("📏 查詢目前分辨率", "FD FC FB FA 02 00 11 00 04 03 02 01"),
            ("🎯 設定0.75m分辨率", "FD FC FB FA 08 00 01 00 00 00 00 00 00 00 04 03 02 01"),
            ("🎯 設定0.5m分辨率", "FD FC FB FA 08 00 01 00 01 00 00 00 00 00 04 03 02 01"),
            ("🎯 設定0.2m分辨率", "FD FC FB FA 08 00 01 00 03 00 00 00 00 00 04 03 02 01")
        ]
        
        for i, (name, cmd) in enumerate(resolution_commands):
            btn = ttk.Button(resolution_frame, text=name, command=lambda c=cmd: self.send_command(c), width=25)
            btn.grid(row=i//4, column=i%4, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        for i in range(4):
            resolution_frame.columnconfigure(i, weight=1)
        
        # 2. 波特率設定區域
        baud_frame = ttk.LabelFrame(main_container, text="📡 波特率設定", padding="10")
        baud_frame.pack(fill=tk.X, pady=(0, 10))
        
        baud_commands = [
            ("📡 設定9600bps", "FD FC FB FA 04 00 A1 00 01 00 04 03 02 01"),
            ("📡 設定115200bps", "FD FC FB FA 04 00 A1 00 05 00 04 03 02 01"),
            ("📡 設定256000bps", "FD FC FB FA 04 00 A1 00 07 00 04 03 02 01"),
            ("📡 設定460800bps", "FD FC FB FA 04 00 A1 00 08 00 04 03 02 01")
        ]
        
        for i, (name, cmd) in enumerate(baud_commands):
            btn = ttk.Button(baud_frame, text=name, command=lambda c=cmd: self.send_command(c), width=25)
            btn.grid(row=i//4, column=i%4, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        for i in range(4):
            baud_frame.columnconfigure(i, weight=1)
        
        # 3. 藍牙與網路設定區域
        network_frame = ttk.LabelFrame(main_container, text="🔗 藍牙與網路", padding="10")
        network_frame.pack(fill=tk.X, pady=(0, 10))
        
        network_commands = [
            ("📱 查詢MAC地址", "FD FC FB FA 04 00 A5 00 01 00 04 03 02 01"),
            ("🔗 開啟藍牙", "FD FC FB FA 04 00 A4 00 01 00 04 03 02 01"),
            ("🔗 關閉藍牙", "FD FC FB FA 04 00 A4 00 00 00 04 03 02 01"),
            ("🏭 恢復出廠設定", "FD FC FB FA 02 00 A2 00 04 03 02 01")
        ]
        
        for i, (name, cmd) in enumerate(network_commands):
            btn = ttk.Button(network_frame, text=name, command=lambda c=cmd: self.send_command(c), width=25)
            btn.grid(row=i//4, column=i%4, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        for i in range(4):
            network_frame.columnconfigure(i, weight=1)
        
        # 4. 背景校正與光感控制區域
        advanced_frame = ttk.LabelFrame(main_container, text="🎯 進階功能", padding="10")
        advanced_frame.pack(fill=tk.X, pady=(0, 10))
        
        advanced_commands = [
            ("❓ 查詢背景校正狀態", "FD FC FB FA 02 00 1B 00 04 03 02 01"),
            ("🎯 動態背景校正", "FD FC FB FA 02 00 0B 00 04 03 02 01"),
            ("💡 查詢光感輔助控制", "FD FC FB FA 02 00 1C 00 04 03 02 01"),
            ("💡 關閉光感輔助", "FD FC FB FA 04 00 0C 00 00 00 04 03 02 01")
        ]
        
        for i, (name, cmd) in enumerate(advanced_commands):
            btn = ttk.Button(advanced_frame, text=name, command=lambda c=cmd: self.send_command(c), width=25)
            btn.grid(row=i//4, column=i%4, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        for i in range(4):
            advanced_frame.columnconfigure(i, weight=1)
        
        # 5. 光感輔助控制快速設定
        light_quick_frame = ttk.LabelFrame(main_container, text="💡 光感輔助快速設定", padding="10")
        light_quick_frame.pack(fill=tk.X, pady=(0, 10))
        
        light_commands = [
            ("💡 光感<80觸發", "FD FC FB FA 04 00 0C 00 01 50 04 03 02 01"),
            ("💡 光感>128觸發", "FD FC FB FA 04 00 0C 00 02 80 04 03 02 01"),
            ("💡 光感<100觸發", "FD FC FB FA 04 00 0C 00 01 64 04 03 02 01"),
            ("💡 光感>200觸發", "FD FC FB FA 04 00 0C 00 02 C8 04 03 02 01")
        ]
        
        for i, (name, cmd) in enumerate(light_commands):
            btn = ttk.Button(light_quick_frame, text=name, command=lambda c=cmd: self.send_command(c), width=25)
            btn.grid(row=i//4, column=i%4, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        for i in range(4):
            light_quick_frame.columnconfigure(i, weight=1)
        
        # 6. 進階配置組合功能區域
        combo_frame = ttk.LabelFrame(main_container, text="🎯 組合功能", padding="10")
        combo_frame.pack(fill=tk.X, pady=(0, 10))
        
        combo_commands = [
            ("💡 光感輔助控制設定", self.light_control_setup),
            ("⚙️ 進階配置", self.advanced_config_setup),
            ("🧪 狀態解析測試", self.test_state_parsing),
            ("📊 詳細診斷", self.detailed_diagnostics),
            ("🔍 測試敏感度更新", self.test_sensitivity_update),  # 新增測試功能
            ("📊 強制刷新圖表", self.force_refresh_charts)  # 新增強制刷新功能
        ]
        
        for i, (name, func) in enumerate(combo_commands):
            btn = ttk.Button(combo_frame, text=name, command=func, width=25)
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        for i in range(3):
            combo_frame.columnconfigure(i, weight=1)
        
        # 7. 配置說明區域
        info_frame = ttk.LabelFrame(main_container, text="📝 配置說明", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        info_text = scrolledtext.ScrolledText(info_frame, height=8, font=("Arial", 11),
                                            bg=self.colors['bg_medium'], 
                                            fg=self.colors['fg_secondary'],
                                            insertbackground=self.colors['fg_primary'],
                                            wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True)
        
        config_info = """⚙️ 配置管理說明

🎯 距離分辨率：影響檢測精度和最大距離
   • 0.75m分辨率：最大12米範圍，標準精度
   • 0.5m分辨率：最大8米範圍，中等精度  
   • 0.2m分辨率：最大3.2米範圍，高精度

📡 波特率設定：影響通信速度，設定後需重啟
   • 115200bps：標準速度，兼容性好
   • 256000bps：高速模式，推薦設定
   • 460800bps：最高速度，需確保線材品質

💡 光感輔助控制：根據光線條件自動控制輸出
   • 小於閾值觸發：光線不足時才輸出（如智能照明）
   • 大於閾值觸發：光線充足時才輸出（如日光偵測）

🎯 背景校正：消除環境干擾，提高檢測精度
   • 執行前請確保檢測區域無人員活動
   • 校正過程約需2分鐘，請耐心等待

⚠️ 重要提醒：
   • 距離分辨率和波特率設定後需重啟模組
   • 恢復出廠設定會清除所有自定義配置
   • 建議在測試環境中先驗證配置效果"""
        
        info_text.insert(tk.END, config_info)
        info_text.config(state=tk.DISABLED)
    
    def setup_matplotlib_charts(self, parent):
        """設置matplotlib圖表"""
        # 創建圖表框架
        chart_frame = ttk.Frame(parent)
        chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # 創建matplotlib圖表 - 增加圖表大小以提供更多空間
        self.fig = Figure(figsize=(18, 12), facecolor='#2b2b2b')  # 進一步增加圖表大小
        self.fig.patch.set_facecolor('#2b2b2b')
        
        # 創建子圖 - 2x2布局，調整間距給雷達圖更多空間
        self.ax1 = self.fig.add_subplot(2, 2, 1)  # 移動目標柱狀圖
        self.ax2 = self.fig.add_subplot(2, 2, 2)  # 靜止目標柱狀圖
        self.ax3 = self.fig.add_subplot(2, 2, 3)  # 距離趨勢圖
        self.ax4 = self.fig.add_subplot(2, 2, 4)  # 雷達圖
        
        # 設置深色主題
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.set_facecolor('#3c3c3c')
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['right'].set_color('white')
        
        # 初始化圖表
        self.setup_gate_energy_charts()
        self.setup_distance_trend_chart()
        self.setup_radar_chart()
        
        # 創建canvas
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加工具欄
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar = NavigationToolbar2Tk(self.canvas, chart_frame)
        toolbar.update()
        
        # 調整布局，給雷達圖留出更多空間，特別是右側空間給圖例
        self.fig.tight_layout(pad=4.0, w_pad=3.0, h_pad=3.5, rect=[0.02, 0.02, 0.85, 0.96])  # 右側留15%空間給雷達圖圖例
    
    def setup_gate_energy_charts(self):
        """設置門能量柱狀圖"""
        # 檢查是否有中文字體支援
        has_chinese = 'PingFang SC' in plt.rcParams['font.sans-serif'][0] or 'Arial Unicode MS' in plt.rcParams['font.sans-serif'][0]
        
        if has_chinese:
            # 移動目標能量圖
            self.ax1.set_title('移動目標能量分布', color='#4a9eff', fontsize=14, fontweight='bold')
            self.ax1.set_xlabel('門號', color='white')
            self.ax1.set_ylabel('能量值', color='white')
            
            # 靜止目標能量圖
            self.ax2.set_title('靜止目標能量分布', color='#ef4444', fontsize=14, fontweight='bold')
            self.ax2.set_xlabel('門號', color='white')
            self.ax2.set_ylabel('能量值', color='white')
        else:
            # 使用英文標籤
            self.ax1.set_title('Moving Target Energy', color='#4a9eff', fontsize=14, fontweight='bold')
            self.ax1.set_xlabel('Gate Number', color='white')
            self.ax1.set_ylabel('Energy Level', color='white')
            
            self.ax2.set_title('Static Target Energy', color='#ef4444', fontsize=14, fontweight='bold')
            self.ax2.set_xlabel('Gate Number', color='white')
            self.ax2.set_ylabel('Energy Level', color='white')
        
        self.ax1.set_ylim(0, 100)
        self.ax1.grid(True, alpha=0.3)
        self.ax2.set_ylim(0, 100)
        self.ax2.grid(True, alpha=0.3)
        
        # 初始化空數據
        self.gate_numbers = list(range(14))
        self.moving_bars = self.ax1.bar(self.gate_numbers, [0]*14, color='#4a9eff', alpha=0.8)
        self.still_bars = self.ax2.bar(self.gate_numbers, [0]*14, color='#ef4444', alpha=0.8)
        
        # 不再添加平均敏感度參考線 - 改用個別門敏感度標記
        self.moving_ref_line = None
        self.still_ref_line = None
        
        # 初始化個別門敏感度標記的容器
        self.moving_sensitivity_markers = []
        self.still_sensitivity_markers = []
        self.moving_sensitivity_texts = []
        self.still_sensitivity_texts = []
    
    def setup_distance_trend_chart(self):
        """設置距離趨勢圖"""
        # 檢查是否有中文字體支援
        has_chinese = 'PingFang SC' in plt.rcParams['font.sans-serif'][0] or 'Arial Unicode MS' in plt.rcParams['font.sans-serif'][0]
        
        if has_chinese:
            self.ax3.set_title('檢測距離趨勢', color='#4ade80', fontsize=14, fontweight='bold')
            self.ax3.set_xlabel('時間點', color='white')
            self.ax3.set_ylabel('距離 (cm)', color='white')
            moving_label = '移動距離'
            still_label = '靜止距離'
        else:
            self.ax3.set_title('Distance Trend', color='#4ade80', fontsize=14, fontweight='bold')
            self.ax3.set_xlabel('Time Point', color='white')
            self.ax3.set_ylabel('Distance (cm)', color='white')
            moving_label = 'Moving Distance'
            still_label = 'Static Distance'
            
        self.ax3.grid(True, alpha=0.3)
        
        # 初始化趨勢線
        self.distance_line, = self.ax3.plot([], [], color='#4ade80', linewidth=2, marker='o', markersize=4)
        self.moving_line, = self.ax3.plot([], [], color='#4a9eff', linewidth=1, alpha=0.7, label=moving_label)
        self.still_line, = self.ax3.plot([], [], color='#ef4444', linewidth=1, alpha=0.7, label=still_label)
        
        self.ax3.legend()
    
    def setup_radar_chart(self):
        """設置雷達圖"""
        # 移除原來的ax4，重新創建為極座標軸
        self.ax4.remove()
        self.ax4 = self.fig.add_subplot(2, 2, 4, projection='polar')
        
        # 設置深色主題
        self.ax4.set_facecolor('#3c3c3c')
        self.ax4.tick_params(colors='white', labelsize=8)  # 調整標籤字體大小
        self.ax4.grid(True, color='white', alpha=0.3)
        
        # 檢查是否有中文字體支援
        has_chinese = 'PingFang SC' in plt.rcParams['font.sans-serif'][0] or 'Arial Unicode MS' in plt.rcParams['font.sans-serif'][0]
        
        if has_chinese:
            self.ax4.set_title('門能量雷達圖', color='#fbbf24', fontsize=12, fontweight='bold', pad=15)  # 減少標題間距
            moving_label = '移動目標'
            still_label = '靜止目標'
            gate_labels = [f'門{i:02d}' for i in range(14)]
        else:
            self.ax4.set_title('Gate Energy Radar', color='#fbbf24', fontsize=12, fontweight='bold', pad=15)
            moving_label = 'Moving Target'
            still_label = 'Static Target'
            gate_labels = [f'G{i:02d}' for i in range(14)]
        
        # 創建雷達圖的角度
        self.radar_angles = np.linspace(0, 2 * np.pi, 14, endpoint=False).tolist()
        self.radar_angles += self.radar_angles[:1]  # 閉合圖形
        
        # 初始化雷達圖線條
        self.radar_moving, = self.ax4.plot([], [], 'o-', linewidth=2, color='#4a9eff', alpha=0.8, label=moving_label, markersize=4)
        self.radar_still, = self.ax4.plot([], [], 'o-', linewidth=2, color='#ef4444', alpha=0.8, label=still_label, markersize=4)
        
        # 設置雷達圖格式
        self.ax4.set_theta_offset(np.pi / 2)
        self.ax4.set_theta_direction(-1)
        self.ax4.set_ylim(0, 100)
        
        # 調整圖例位置，避免遮擋雷達圖 - 往右移動200像素
        self.ax4.legend(loc='upper right', bbox_to_anchor=(1.8, 1.1), fontsize=9)  # 從1.3調整到1.8，增加約200像素的距離
        
        # 設置門號標籤，減少字體大小避免擁擠
        self.ax4.set_thetagrids(np.degrees(self.radar_angles[:-1]), gate_labels, fontsize=8)
        
        # 設置徑向標籤
        self.ax4.set_ylim(0, 100)
        self.ax4.set_yticks([20, 40, 60, 80, 100])
        self.ax4.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=7)
    
    def on_chart_type_change(self, event=None):
        """圖表類型改變事件"""
        chart_type = self.chart_type_var.get()
        self.log(f"📊 切換圖表類型: {chart_type}")
        # 重新繪製圖表
        if hasattr(self, 'current_data') and self.current_data:
            self.update_matplotlib_charts()
    
    def toggle_chart_freeze(self):
        """切換圖表凍結狀態"""
        self.chart_frozen = not self.chart_frozen
        if self.chart_frozen:
            self.freeze_btn.config(text="🔥 解凍圖表")
            self.log("❄️ 圖表已凍結")
        else:
            self.freeze_btn.config(text="❄️ 凍結圖表")
            self.log("🔥 圖表已解凍")
    
    def save_chart(self):
        """保存圖表"""
        try:
            from tkinter import filedialog
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("SVG files", "*.svg")],
                initialname=f"LD2412_chart_{timestamp}"
            )
            if filename:
                self.fig.savefig(filename, dpi=300, bbox_inches='tight', facecolor='#2b2b2b')
                self.log(f"💾 圖表已保存: {filename}")
        except Exception as e:
            self.log(f"❌ 保存失敗: {e}")
    
    def create_raw_data_tab(self):
        """創建原始數據分頁"""
        raw_tab = ttk.Frame(self.notebook)
        self.notebook.add(raw_tab, text="🔢 原始數據")
        
        # 只顯示原始16進制數據
        raw_frame = ttk.LabelFrame(raw_tab, text="原始16進制數據流", padding="5")
        raw_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.raw_text = scrolledtext.ScrolledText(raw_frame, font=("Courier", 12),
                                                bg=self.colors['bg_light'], 
                                                fg=self.colors['accent_green'],
                                                insertbackground=self.colors['fg_primary'])
        self.raw_text.pack(fill=tk.BOTH, expand=True)
    
    def create_detailed_analysis_tab(self):
        """創建詳細解析分頁"""
        detailed_tab = ttk.Frame(self.notebook)
        self.notebook.add(detailed_tab, text="📋 詳細解析")
        
        # 詳細解析顯示
        detailed_frame = ttk.LabelFrame(detailed_tab, text="詳細解析報告", padding="5")
        detailed_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.detailed_text = scrolledtext.ScrolledText(detailed_frame, font=("Courier", 12),
                                                     bg=self.colors['bg_light'], 
                                                     fg=self.colors['fg_primary'],
                                                     insertbackground=self.colors['fg_primary'])
        self.detailed_text.pack(fill=tk.BOTH, expand=True)
    
    def start_data_thread(self):
        """啟動數據讀取線程"""
        self.data_thread = threading.Thread(target=self.data_reader, daemon=True)
        self.data_thread.start()
    
    def data_reader(self):
        """數據讀取線程 - 高速版本"""
        consecutive_errors = 0
        max_read_size = 512  # 進一步增加讀取緩衝區大小
        
        while True:
            if self.is_connected and self.serial_port and self.is_monitoring:
                try:
                    # 檢查是否有數據可讀
                    if self.serial_port.in_waiting > 0:
                        # 限制每次讀取的數據量
                        bytes_to_read = min(self.serial_port.in_waiting, max_read_size)
                        data = self.serial_port.read(bytes_to_read)
                        
                        if data:
                            self.data_queue.put(('data', data))
                            consecutive_errors = 0  # 重置錯誤計數
                        
                        # 如果有命令等待回應，優先處理
                        if self.waiting_for_response:
                            time.sleep(0.001)  # 極小延遲
                        elif bytes_to_read >= max_read_size:
                            time.sleep(0.005)  # 減少延遲
                    
                    # 正常延遲 - 配置模式下更快響應
                    if self.waiting_for_response or self.is_config_mode:
                        time.sleep(0.001)  # 配置模式或等待回應時極快
                    else:
                        time.sleep(0.005)  # 正常情況下適中
                    
                except SerialException as e:
                    consecutive_errors += 1
                    self.data_queue.put(('error', f"串列埠錯誤: {e}"))
                    
                    # 如果連續錯誤過多，停止監控
                    if consecutive_errors > 10:
                        self.data_queue.put(('disconnect', "連續錯誤過多，自動斷開連接"))
                        break
                    
                    time.sleep(0.02)
                    
                except Exception as e:
                    consecutive_errors += 1
                    self.data_queue.put(('error', f"未知錯誤: {e}"))
                    
                    if consecutive_errors > 5:
                        self.data_queue.put(('disconnect', "嚴重錯誤，自動斷開連接"))
                        break
                    
                    time.sleep(0.05)
            else:
                time.sleep(0.02)  # 未連接時減少延遲
    
    def update_display(self):
        """更新顯示 - 高速版本"""
        processed_count = 0
        max_process_per_cycle = 15  # 進一步增加每次處理的消息數量
        
        # 處理數據隊列
        while not self.data_queue.empty() and processed_count < max_process_per_cycle:
            try:
                msg_type, data = self.data_queue.get_nowait()
                processed_count += 1
                
                if msg_type == 'data':
                    self.process_data(data)
                elif msg_type == 'error':
                    self.log(f"❌ 錯誤: {data}")
                elif msg_type == 'disconnect':
                    self.log(f"⚠️ 自動斷開: {data}")
                    self.auto_disconnect()
                    
            except queue.Empty:
                break
            except Exception as e:
                self.log(f"❌ 顯示更新錯誤: {e}")
                break
        
        # 檢查命令超時
        if self.waiting_for_response:
            if time.time() - self.last_command_time > self.command_timeout:
                self.waiting_for_response = False
        
        # 更新顯示內容
        try:
            self.update_realtime_display()
            self.update_stats_display()
            self.update_chart_display()
        except Exception as e:
            self.log(f"❌ 界面更新錯誤: {e}")
        
        # 繼續更新 - 配置模式和等待回應時更快更新
        if self.waiting_for_response or self.is_config_mode:
            update_interval = 20  # 配置模式下極快更新
        else:
            update_interval = 80  # 正常模式
        self.root.after(update_interval, self.update_display)
    
    def process_data(self, data):
        """處理接收到的數據 - 優化版本：命令回應立即分析，數據幀定時分析"""
        # 限制緩衝區大小
        if len(self.raw_buffer) > 3000:
            self.raw_buffer = self.raw_buffer[-1500:]  # 保留最近的數據
        
        self.raw_buffer.extend(data)
        
        # 顯示原始數據（限制長度）
        if len(data) <= 256:  # 只顯示較小的數據包
            hex_str = ' '.join([f'{b:02X}' for b in data])
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.add_text(self.raw_text, f"[{timestamp}] {hex_str}\n")
        else:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.add_text(self.raw_text, f"[{timestamp}] [大數據包: {len(data)} 字節]\n")
        
        # 如果正在等待命令回應，立即檢查是否有命令回應幀
        if self.waiting_for_response:
            try:
                self.check_immediate_command_response()
            except Exception as e:
                self.log(f"❌ 命令回應分析錯誤: {e}")
        
        # 定時分析機制 - 每0.1秒分析一次（主要用於數據幀）
        current_time = time.time()
        if current_time - self.last_analysis_time >= self.analysis_interval:
            self.last_analysis_time = current_time
            try:
                self.analyze_one_frame()
            except Exception as e:
                self.log(f"❌ 定時分析錯誤: {e}")
    
    def check_immediate_command_response(self):
        """立即檢查命令回應幀 - 用於配置模式下的即時回應"""
        buffer = bytes(self.raw_buffer)
        
        if len(buffer) < 8:  # 最小命令回應幀長度
            return
        
        # 從最新的數據開始搜索命令回應幀
        for i in range(len(buffer) - 7, -1, -1):  # 從後往前搜索
            # 命令回應幀頭 FD FC FB FA
            if buffer[i:i+4] == b'\xFD\xFC\xFB\xFA':
                # 檢查數據長度字段
                if i + 6 < len(buffer):
                    data_length = buffer[i+4] | (buffer[i+5] << 8)
                    expected_frame_length = 6 + 2 + data_length + 4  # 頭(4) + 長度(2) + 數據 + 尾(4)
                    
                    # 如果緩衝區有足夠的數據
                    if i + expected_frame_length <= len(buffer):
                        # 檢查幀尾
                        tail_start = i + expected_frame_length - 4
                        if buffer[tail_start:tail_start+4] == b'\x04\x03\x02\x01':
                            frame = buffer[i:i+expected_frame_length]
                            
                            # 立即解析命令回應
                            frame_hex = ' '.join([f'{b:02X}' for b in frame])
                            print(f"立即發現命令回應幀: {frame_hex}")
                            self.parse_command_response(frame)
                            
                            # 清理已處理的數據
                            self.raw_buffer = self.raw_buffer[i+expected_frame_length:]
                            return
                
                # 如果基於長度的方法失敗，使用固定長度搜索
                for j in range(i + 8, min(i + 40, len(buffer) - 3)):  # 減少搜索範圍
                    if buffer[j:j+4] == b'\x04\x03\x02\x01':
                        frame = buffer[i:j+4]
                        
                        # 立即解析命令回應
                        frame_hex = ' '.join([f'{b:02X}' for b in frame])
                        print(f"立即發現命令回應幀(固定): {frame_hex}")
                        self.parse_command_response(frame)
                        
                        # 清理已處理的數據
                        self.raw_buffer = self.raw_buffer[j+4:]
                        return
    
    def analyze_one_frame(self):
        """定時分析：從緩衝區中尋找並分析一個完整幀 - 基於官方LD2412庫實現"""
        buffer = bytes(self.raw_buffer)
        
        if len(buffer) < 12:  # 官方庫要求最小12字節
            return
        
        # 尋找最完整的數據幀
        best_frame = None
        best_score = 0
        
        # 查找所有可能的幀頭位置
        for i in range(len(buffer) - 11):
            # 數據幀頭 F4 F3 F2 F1 (官方庫定義)
            if buffer[i:i+4] == b'\xF4\xF3\xF2\xF1':
                # 查找數據幀尾 F8 F7 F6 F5 (官方庫定義)
                for j in range(i + 12, min(i + 80, len(buffer) - 3)):  # 官方庫最大長度約80字節
                    if buffer[j:j+4] == b'\xF8\xF7\xF6\xF5':
                        frame = buffer[i:j+4]
                        
                        # 驗證幀結構 (根據官方庫)
                        if len(frame) >= 12:
                            # 檢查常數值：第7字節=0xAA, 倒數第6字節=0x55
                            if frame[7] == 0xAA and frame[-6] == 0x55:
                                frame_len = len(frame)
                                # 正常模式數據幀(~21字節)和工程模式數據幀(~51字節)都給高分
                                if frame_len >= 20:  # 正常模式最小長度
                                    score = 80 + frame_len  # 基礎高分 + 長度獎勵
                                else:
                                    score = frame_len  # 短幀低分
                                if score > best_score:
                                    best_frame = frame
                                    best_score = score
                        break
            
            # 命令回應幀頭 FD FC FB FA (官方庫定義)
            elif buffer[i:i+4] == b'\xFD\xFC\xFB\xFA':
                # 檢查數據長度字段
                if i + 6 < len(buffer):
                    data_length = buffer[i+4] | (buffer[i+5] << 8)
                    expected_frame_length = 6 + 2 + data_length + 4  # 頭(4) + 長度(2) + 數據 + 尾(4)
                    
                    # 如果緩衝區有足夠的數據
                    if i + expected_frame_length <= len(buffer):
                        # 檢查幀尾
                        tail_start = i + expected_frame_length - 4
                        if buffer[tail_start:tail_start+4] == b'\x04\x03\x02\x01':
                            frame = buffer[i:i+expected_frame_length]
                            score = 60  # 命令回應幀得較高分數
                            if score > best_score:
                                best_frame = frame
                                best_score = score
                            continue
                
                # 如果基於長度的方法失敗，使用舊方法
                for j in range(i + 8, min(i + 60, len(buffer) - 3)):
                    if buffer[j:j+4] == b'\x04\x03\x02\x01':
                        frame = buffer[i:j+4]
                        score = 50  # 命令回應幀得中等分數
                        if score > best_score:
                            best_frame = frame
                            best_score = score
                        break
        
        # 分析最佳幀
        if best_frame and best_score >= 50:
            try:
                if best_frame[0:4] == b'\xF4\xF3\xF2\xF1':
                    frame_hex = ' '.join([f'{b:02X}' for b in best_frame])
                    print(f"找到數據幀 (長度={len(best_frame)}, 得分={best_score}): {frame_hex}")
                    self.parse_periodic_data(best_frame)
                elif best_frame[0:4] == b'\xFD\xFC\xFB\xFA':
                    # 調試信息：顯示找到的命令回應幀
                    frame_hex = ' '.join([f'{b:02X}' for b in best_frame])
                    print(f"找到命令回應幀 (長度={len(best_frame)}): {frame_hex}")
                    self.parse_command_response(best_frame)
                    
                # 分析完成後，保守地清理緩衝區
                if len(self.raw_buffer) > 1000:
                    self.raw_buffer = self.raw_buffer[-500:]
                    
            except Exception as e:
                self.log(f"❌ 幀分析錯誤: {e}")
        else:
            # 如果沒有找到完整幀，但找到了命令回應頭，顯示調試信息
            for i in range(len(buffer) - 3):
                if buffer[i:i+4] == b'\xFD\xFC\xFB\xFA':
                    partial_data = buffer[i:min(i+20, len(buffer))]
                    partial_hex = ' '.join([f'{b:02X}' for b in partial_data])
                    print(f"發現命令回應頭但幀不完整: {partial_hex}...")
                    break

    def parse_periodic_data(self, frame):
        """解析週期性數據幀 - 基於協議文檔實現"""
        if len(frame) < 21:  # 一般模式最小幀長度
            print(f"幀太短: {len(frame)} < 21")
            return
            
        # 協議文檔驗證檢查
        if (frame[0] != 0xF4 or frame[1] != 0xF3 or 
            frame[2] != 0xF2 or frame[3] != 0xF1):
            print(f"幀頭錯誤: {frame[0]:02X} {frame[1]:02X} {frame[2]:02X} {frame[3]:02X}")
            return
            
        # 檢查幀尾
        if (frame[-4] != 0xF8 or frame[-3] != 0xF7 or 
            frame[-2] != 0xF6 or frame[-1] != 0xF5):
            print(f"幀尾錯誤: {frame[-4]:02X} {frame[-3]:02X} {frame[-2]:02X} {frame[-1]:02X}")
            return
            
        # 檢查校驗字節和尾部標識
        if frame[7] != 0xAA:  # 校驗字節
            print(f"校驗字節錯誤: frame[7]=0x{frame[7]:02X}, 應該是0xAA")
            return
            
        # 檢查尾部標識（工程模式在47位置，一般模式在15位置）
        data_type = frame[6]
        if data_type == 0x01:  # 工程模式
            if len(frame) < 53 or frame[47] != 0x55:
                print(f"工程模式尾部標識錯誤: frame[47]=0x{frame[47]:02X}, 應該是0x55")
                return
        elif data_type == 0x02:  # 一般模式
            if len(frame) < 21 or frame[15] != 0x55:
                print(f"一般模式尾部標識錯誤: frame[15]=0x{frame[15]:02X}, 應該是0x55")
                return
        
        self.stats['total_frames'] += 1
        
        # 根據協議文檔的數據幀結構解析
        frame_length = frame[4] | (frame[5] << 8)      # 第4-5字節：數據長度（小端序）
        target_state = frame[8]                         # 第8字節：目標狀態
        
        # 基本距離和能量數據（協議文檔字節位置）
        move_dist = frame[9] | (frame[10] << 8)         # 第9-10字節：移動目標距離（小端序）
        move_energy = frame[11]                         # 第11字節：移動目標能量值
        still_dist = frame[12] | (frame[13] << 8)       # 第12-13字節：靜止目標距離（小端序）
        still_energy = frame[14]                        # 第14字節：靜止目標能量值
        
        # 判斷模式
        engineering_mode = (data_type == 0x01)          # 0x01=工程模式, 0x02=一般模式
        
        # 光感值和門能量數據（僅工程模式）
        light_value = 0
        moving_gate_energies = []
        still_gate_energies = []
        moving_gates_count = 0
        still_gates_count = 0
        
        if engineering_mode and len(frame) >= 53:  # 協議文檔要求的工程模式最小長度
            # 根據協議文檔的工程模式數據幀結構
            moving_gates_count = frame[15]              # 第15字節：移動能量門數量（0D=13，代表0-13共14門）
            still_gates_count = frame[16]               # 第16字節：靜止能量門數量（0D=13，代表0-13共14門）
            
            # 移動目標各門能量（第17-30字節，14個門）
            moving_gate_energies = list(frame[17:31])
            
            # 靜止目標各門能量（第31-44字節，14個門）
            still_gate_energies = list(frame[31:45])
            
            # 光感數據（第45字節）
            light_value = frame[45]
            
            # 保留字節和尾部標識（第46-48字節）
            reserved1 = frame[46]  # 保留字節1
            tail_marker = frame[47]  # 尾部標識，應該是0x55
            reserved2 = frame[48]  # 保留字節2
        
        # 檢測距離計算
        detect_dist = max(move_dist, still_dist) if move_dist > 0 or still_dist > 0 else 0
        
        # 更新數據
        self.update_data_history(move_dist, move_energy, still_dist, still_energy, detect_dist, target_state, light_value)
        
        mode = '工程模式' if engineering_mode else '一般模式'
        self.current_data = {
            'timestamp': datetime.now(),
            'mode': mode,
            'state': target_state,
            'move_dist': move_dist,
            'move_energy': move_energy,
            'still_dist': still_dist,
            'still_energy': still_energy,
            'detect_dist': detect_dist,
            'light': light_value,
            'frame_len': len(frame),
            'data_type': data_type,
            'frame_length': frame_length,
            'head_byte': frame[7],
            'moving_gate_energies': moving_gate_energies,
            'still_gate_energies': still_gate_energies,
            'moving_gates_count': moving_gates_count,
            'still_gates_count': still_gates_count
        }
        
        # 顯示解析結果
        self.display_parsed_result(engineering_mode)
        
        # 檢查警報
        self.check_alerts(detect_dist, move_energy, still_energy)

    def display_parsed_result(self, engineering_mode):
        """顯示解析結果"""
        data = self.current_data
        state_text = self.get_state_text(data['state'])
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if engineering_mode:
            # 格式化門能量顯示 - 根據協議文檔更新
            moving_info = ""
            moving_energies = data.get('moving_gate_energies', [])
            if moving_energies and len(moving_energies) >= 8:
                for i in range(min(len(moving_energies), 14)):
                    if i % 7 == 0:  # 每行顯示7個門
                        moving_info += f"\n移動門{i:2d}-{min(i+6, 13):2d}: "
                    moving_info += f"{moving_energies[i]:3d} "
            
            still_info = ""
            still_energies = data.get('still_gate_energies', [])
            if still_energies and len(still_energies) >= 8:
                for i in range(min(len(still_energies), 14)):
                    if i % 7 == 0:  # 每行顯示7個門
                        still_info += f"\n靜止門{i:2d}-{min(i+6, 13):2d}: "
                    still_info += f"{still_energies[i]:3d} "
            
            # 距離門說明
            gate_count = data.get('moving_gates_count', 13)
            gate_info = f"距離門範圍: 0-{gate_count} (共{gate_count+1}門), 每門0.75m"
            
            result = f"""[{timestamp}] 📡 工程模式數據幀 #{self.stats['total_frames']}
幀結構: 長度={data['frame_len']}字節, 數據類型=0x{data['data_type']:02X}, 校驗=0x{data['head_byte']:02X}
目標狀態: {state_text} (0x{data['state']:02X})
基本數據: 移動距離={data['move_dist']:4d}cm/能量={data['move_energy']:3d}, 靜止距離={data['still_dist']:4d}cm/能量={data['still_energy']:3d}
光感數據: {data['light']:3d} (0x{data['light']:02X}) - 範圍0-255，值越大表示光線越強
檢測距離: {data['detect_dist']:4d}cm (綜合距離)
{gate_info}
門能量分布:{moving_info}{still_info}
{"="*60}
"""
        else:
            result = f"""[{timestamp}] 📊 一般模式數據幀 #{self.stats['total_frames']}
幀結構: 長度={data['frame_len']}字節, 數據類型=0x{data['data_type']:02X}, 校驗=0x{data['head_byte']:02X}
目標狀態: {state_text} (0x{data['state']:02X})
基本數據: 移動距離={data['move_dist']:4d}cm/能量={data['move_energy']:3d}, 靜止距離={data['still_dist']:4d}cm/能量={data['still_energy']:3d}
檢測距離: {data['detect_dist']:4d}cm
光感數據: {data['light']:3d} (工程模式下可用)
💡 提示: 開啟工程模式可查看詳細門能量分布
{"="*60}
"""
        
        self.add_text(self.detailed_text, result)

    def parse_frame(self, frame):
        """舊的解析函數 - 保持向後兼容"""
        # 重定向到新的解析函數
        self.parse_periodic_data(frame)

    def parse_normal_mode(self, frame):
        """舊的正常模式解析函數 - 保持向後兼容"""
        pass

    def parse_engineering_mode(self, frame):
        """舊的工程模式解析函數 - 保持向後兼容"""
        pass
    
    def update_data_history(self, move_dist, move_energy, still_dist, still_energy, detect_dist, target_state, light_value):
        """更新數據歷史記錄"""
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
        self.update_statistics(target_state, detect_dist)
    
    def update_statistics(self, state, detect_dist):
        """更新統計數據 - 根據協議文檔修正"""
        # 根據協議文檔的狀態值進行統計
        if state == 0x01:  # 運動目標
            self.stats['moving_detections'] += 1
        elif state == 0x02:  # 靜止目標
            self.stats['still_detections'] += 1
        elif state == 0x03:  # 運動&靜止目標
            self.stats['moving_detections'] += 1
            self.stats['still_detections'] += 1
        elif state == 0x00:  # 無目標
            self.stats['no_target'] += 1
        # 0x04-0x06 是底噪檢測狀態，不計入目標統計
        
        # 更新距離統計（只有在有目標時才統計距離）
        if state in [0x01, 0x02, 0x03] and detect_dist > 0:
            self.stats['max_distance'] = max(self.stats['max_distance'], detect_dist)
            if self.stats['min_distance'] == 9999:
                self.stats['min_distance'] = detect_dist
            else:
                self.stats['min_distance'] = min(self.stats['min_distance'], detect_dist)
        
        self.stats['last_update'] = time.time()
    
    def check_alerts(self, distance, move_energy, still_energy):
        """檢查警報"""
        alerts = []
        
        # 近距離警報
        if 0 < distance < 50:
            alerts.append(f"⚠️ 近距離警報: {distance}cm")
        
        # 不再記錄能量警報到日誌
        # 能量信息只在數據顯示區域顯示
        
        # 顯示警報
        for alert in alerts:
            self.log(alert)
    
    def get_state_text(self, state):
        """獲取狀態文字描述 - 根據協議文檔修正"""
        # 根據協議文檔的目標狀態位解析表
        state_map = {
            0x00: "❌ 無目標",
            0x01: "🏃 運動目標", 
            0x02: "🧍 靜止目標",
            0x03: "🏃🧍 運動&靜止目標",
            0x04: "🔍 正在底噪檢測中",
            0x05: "✅ 底噪檢測成功", 
            0x06: "❌ 底噪檢測失敗"
        }
        
        return state_map.get(state, f"❓ 未知狀態(0x{state:02X})")
    
    def update_realtime_display(self):
        """更新即時數據顯示"""
        try:
            if self.current_data:
                data = self.current_data
                state_text = self.get_state_text(data['state'])
                mode = data.get('mode', '未知')
                
                # 基本信息顯示
                realtime_info = f"""╔══════════════════════════════════════════════════╗
║                   即時數據分析                     ║
╠══════════════════════════════════════════════════╣
║ 工作模式: {mode:<30} ║
║ 目標狀態: {state_text:<30} ║
║ 移動距離: {data['move_dist']:4d} cm    移動能量: {data['move_energy']:3d}     ║
║ 靜止距離: {data['still_dist']:4d} cm    靜止能量: {data['still_energy']:3d}     ║
║ 檢測距離: {data['detect_dist']:4d} cm    光感值:  {data['light']:3d}     ║"""
                
                # 如果是工程模式，顯示門能量信息
                if mode == '工程模式' and 'moving_gate_energies' in data:
                    moving_energies = data['moving_gate_energies']
                    still_energies = data.get('still_gate_energies', [])
                    
                    # 安全檢查：確保是列表類型
                    if isinstance(moving_energies, list) and moving_energies:
                        realtime_info += f"""║                                                  ║
║ 移動門能量值:                                    ║"""
                        
                        # 每行顯示4個門的移動能量
                        for i in range(0, min(len(moving_energies), 8), 4):
                            gate_line = "║ "
                            for j in range(4):
                                if i + j < len(moving_energies):
                                    try:
                                        energy = int(moving_energies[i+j])
                                        gate_line += f"門{i+j:2d}:{energy:3d} "
                                    except (ValueError, TypeError):
                                        gate_line += f"門{i+j:2d}:--- "
                                else:
                                    gate_line += "      "
                            gate_line += " " * (50 - len(gate_line)) + "║"
                            realtime_info += f"\n{gate_line}"
                    
                    if isinstance(still_energies, list) and still_energies:
                        realtime_info += f"""║                                                  ║
║ 靜止門能量值:                                    ║"""
                        
                        # 每行顯示4個門的靜止能量
                        for i in range(0, min(len(still_energies), 8), 4):
                            gate_line = "║ "
                            for j in range(4):
                                if i + j < len(still_energies):
                                    try:
                                        energy = int(still_energies[i+j])
                                        gate_line += f"門{i+j:2d}:{energy:3d} "
                                    except (ValueError, TypeError):
                                        gate_line += f"門{i+j:2d}:--- "
                                else:
                                    gate_line += "      "
                            gate_line += " " * (50 - len(gate_line)) + "║"
                            realtime_info += f"\n{gate_line}"
                
                realtime_info += f"""║                                                  ║
║ 幀長度: {data['frame_len']:2d} 字節  數據類型: 0x{data.get('data_type', 0):02X}            ║
║ 最後更新: {data['timestamp'].strftime('%H:%M:%S.%f')[:-3]:<30} ║
╚══════════════════════════════════════════════════╝"""
            else:
                realtime_info = """╔══════════════════════════════════════════════════╗
║                   即時數據分析                     ║
╠══════════════════════════════════════════════════╣
║ 工作模式: 等待數據...                            ║
║ 目標狀態: 等待數據...                            ║
║ 移動距離:   -- cm    移動能量:  --              ║
║ 靜止距離:   -- cm    靜止能量:  --              ║
║ 檢測距離:   -- cm    光感值:   --              ║
║                                                  ║
║ 請先連接設備並開始監控                           ║
╚══════════════════════════════════════════════════╝"""
            
            self.realtime_text.delete(1.0, tk.END)
            self.realtime_text.insert(1.0, realtime_info)
            
        except Exception as e:
            # 如果即時顯示更新失敗，顯示錯誤信息
            error_info = f"""╔══════════════════════════════════════════════════╗
║                   即時數據分析                     ║
╠══════════════════════════════════════════════════╣
║ 顯示更新錯誤: {str(e)[:40]:<40} ║
║                                                  ║
║ 請檢查數據格式或重新連接設備                     ║
╚══════════════════════════════════════════════════╝"""
            self.realtime_text.delete(1.0, tk.END)
            self.realtime_text.insert(1.0, error_info)
    
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
    
    def update_chart_display(self):
        """更新門能量分布圖 - 根據可用性選擇實現"""
        try:
            # 如果圖表被凍結，不更新
            if hasattr(self, 'chart_frozen') and self.chart_frozen:
                return
            
            # 根據matplotlib可用性選擇實現
            if MATPLOTLIB_AVAILABLE and hasattr(self, 'fig'):
                self.update_matplotlib_charts()
            else:
                self.update_text_charts()
            
        except Exception as e:
            import traceback
            print(f"圖表更新錯誤: {e}")
            print(traceback.format_exc())
    
    def update_matplotlib_charts(self):
        """更新matplotlib圖表"""
        try:
            # 檢查是否有當前數據
            if not self.current_data:
                return
            
            # 獲取數據
            moving_energies = self.current_data.get('moving_gate_energies', [])
            still_energies = self.current_data.get('still_gate_energies', [])
            
            # 數據安全處理
            safe_moving = self.safe_convert_energies(moving_energies)
            safe_still = self.safe_convert_energies(still_energies)
            
            # 確保有14個門的數據
            safe_moving = (safe_moving + [0] * 14)[:14]
            safe_still = (safe_still + [0] * 14)[:14]
            
            # 更新柱狀圖
            if hasattr(self, 'moving_bars') and hasattr(self, 'still_bars'):
                for i, (bar_m, bar_s) in enumerate(zip(self.moving_bars, self.still_bars)):
                    bar_m.set_height(safe_moving[i])
                    bar_s.set_height(safe_still[i])
                    
                    # 為每個柱狀圖設定顏色：超過敏感度閾值的門使用更亮的顏色
                    if i < len(self.moving_gate_sensitivities):
                        if safe_moving[i] >= self.moving_gate_sensitivities[i]:
                            bar_m.set_color('#66b3ff')  # 亮藍色（超過閾值）
                        else:
                            bar_m.set_color('#4a9eff')  # 正常藍色
                    
                    if i < len(self.still_gate_sensitivities):
                        if safe_still[i] >= self.still_gate_sensitivities[i]:
                            bar_s.set_color('#ff6666')  # 亮紅色（超過閾值）
                        else:
                            bar_s.set_color('#ef4444')  # 正常紅色
                
                # 動態調整Y軸範圍
                max_energy = max(max(safe_moving), max(safe_still), 50)
                self.ax1.set_ylim(0, max_energy * 1.1)
                self.ax2.set_ylim(0, max_energy * 1.1)
                
                # 在圖表上顯示每個門的敏感度線（小標記）
                self.draw_individual_sensitivity_markers()
            
            # 更新距離趨勢圖
            self.update_distance_trend()
            
            # 更新雷達圖
            self.update_radar_chart(safe_moving, safe_still)
            
            # 更新圖表標題（顯示當前狀態）
            if self.current_data.get('mode') == '工程模式':
                timestamp = self.current_data.get('timestamp', datetime.now())
                light_value = self.current_data.get('light', 0)
                detect_dist = self.current_data.get('detect_dist', 0)
                
                self.ax1.set_title(f'🏃 移動目標能量分布\n{timestamp.strftime("%H:%M:%S")} | 光感:{light_value} | 距離:{detect_dist}cm', 
                                  color='#4a9eff', fontsize=12)
                self.ax2.set_title(f'🧍 靜止目標能量分布\n{timestamp.strftime("%H:%M:%S")} | 光感:{light_value} | 距離:{detect_dist}cm', 
                                  color='#ef4444', fontsize=12)
            
            # 重新繪製
            self.canvas.draw_idle()
            
        except Exception as e:
            print(f"matplotlib圖表更新錯誤: {e}")
    
    def safe_convert_energies(self, energies):
        """安全轉換能量數據"""
        safe_list = []
        if not isinstance(energies, (list, tuple)):
            return safe_list
            
        for i, item in enumerate(energies):
            try:
                if isinstance(item, (int, float)):
                    safe_list.append(max(0, min(100, int(item))))  # 限制在0-100範圍
                elif isinstance(item, (str, bytes)):
                    safe_list.append(max(0, min(100, int(str(item)))))
                else:
                    safe_list.append(0)
            except (ValueError, TypeError):
                safe_list.append(0)
        return safe_list
    
    def update_distance_trend(self):
        """更新距離趨勢圖"""
        try:
            # 獲取最近30個數據點
            if len(self.data_history['time']) < 2:
                return
            
            times = list(self.data_history['time'])[-30:]
            detect_distances = list(self.data_history['detection_distance'])[-30:]
            moving_distances = list(self.data_history['moving_distance'])[-30:]
            still_distances = list(self.data_history['still_distance'])[-30:]
            
            # 更新線條數據
            self.distance_line.set_data(times, detect_distances)
            self.moving_line.set_data(times, moving_distances)
            self.still_line.set_data(times, still_distances)
            
            # 動態調整軸範圍
            if times:
                self.ax3.set_xlim(min(times), max(times))
                
            all_distances = detect_distances + moving_distances + still_distances
            valid_distances = [d for d in all_distances if d > 0]
            if valid_distances:
                max_dist = max(valid_distances)
                self.ax3.set_ylim(0, max_dist * 1.1)
            
        except Exception as e:
            print(f"距離趨勢更新錯誤: {e}")
    
    def update_radar_chart(self, moving_energies, still_energies):
        """更新雷達圖"""
        try:
            # 確保數據閉合（首尾相接）
            moving_data = moving_energies + [moving_energies[0]]
            still_data = still_energies + [still_energies[0]]
            
            # 清除舊的圖形
            self.ax4.clear()
            
            # 重新設置極座標軸屬性
            self.ax4.set_facecolor('#3c3c3c')
            self.ax4.tick_params(colors='white', labelsize=8)
            self.ax4.grid(True, color='white', alpha=0.3)
            self.ax4.set_theta_offset(np.pi / 2)
            self.ax4.set_theta_direction(-1)
            self.ax4.set_ylim(0, 100)
            
            # 檢查是否有中文字體支援
            has_chinese = 'PingFang SC' in plt.rcParams['font.sans-serif'][0] or 'Arial Unicode MS' in plt.rcParams['font.sans-serif'][0]
            
            if has_chinese:
                moving_label = '移動目標'
                still_label = '靜止目標'
                gate_labels = [f'門{i:02d}' for i in range(14)]
                title = '🎯 門能量雷達圖'
            else:
                moving_label = 'Moving Target'
                still_label = 'Static Target'
                gate_labels = [f'G{i:02d}' for i in range(14)]
                title = '🎯 Gate Energy Radar'
            
            # 繪製雷達圖
            self.ax4.plot(self.radar_angles, moving_data, 'o-', linewidth=2, color='#4a9eff', 
                         alpha=0.8, label=moving_label, markersize=4)
            self.ax4.fill(self.radar_angles, moving_data, alpha=0.25, color='#4a9eff')
            
            self.ax4.plot(self.radar_angles, still_data, 'o-', linewidth=2, color='#ef4444', 
                         alpha=0.8, label=still_label, markersize=4)
            self.ax4.fill(self.radar_angles, still_data, alpha=0.25, color='#ef4444')
            
            # 設置標題和圖例
            self.ax4.set_title(title, color='#fbbf24', fontsize=12, fontweight='bold', pad=15)
            self.ax4.legend(loc='upper right', bbox_to_anchor=(1.8, 1.1), fontsize=9)  # 從1.3調整到1.8，增加約200像素的距離
            
            # 設置門號標籤
            self.ax4.set_thetagrids(np.degrees(self.radar_angles[:-1]), gate_labels, fontsize=8)
            
            # 設置徑向標籤
            self.ax4.set_yticks([20, 40, 60, 80, 100])
            self.ax4.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=7)
            
        except Exception as e:
            print(f"雷達圖更新錯誤: {e}")
            self.log(f"⚠️ 雷達圖更新失敗: {e}")
    
    def update_sensitivity_reference_lines(self):
        """清除平均敏感度參考線 - 改為只使用個別門敏感度標記"""
        try:
            if not MATPLOTLIB_AVAILABLE or not hasattr(self, 'ax1') or not hasattr(self, 'ax2'):
                return
                
            # 移除舊的平均參考線（如果存在）
            if hasattr(self, 'moving_ref_line') and self.moving_ref_line:
                try:
                    self.moving_ref_line.remove()
                except:
                    pass
                self.moving_ref_line = None
                
            if hasattr(self, 'still_ref_line') and self.still_ref_line:
                try:
                    self.still_ref_line.remove()
                except:
                    pass
                self.still_ref_line = None
            
            # 清除圖例（移除平均敏感度圖例）
            self.ax1.legend().set_visible(False) if self.ax1.get_legend() else None
            self.ax2.legend().set_visible(False) if self.ax2.get_legend() else None
            
            # 更新圖表標題，強調使用個別門敏感度
            current_title1 = self.ax1.get_title()
            base_title1 = current_title1.split('\n')[0] if '\n' in current_title1 else current_title1.split('敏感度:')[0]
            self.ax1.set_title(f'{base_title1}\n🎯 個別門敏感度設定', 
                              color='#4a9eff', fontsize=11, fontweight='bold')
            
            current_title2 = self.ax2.get_title()
            base_title2 = current_title2.split('\n')[0] if '\n' in current_title2 else current_title2.split('敏感度:')[0]
            self.ax2.set_title(f'{base_title2}\n🎯 個別門敏感度設定', 
                              color='#ef4444', fontsize=11, fontweight='bold')
            
            # 立即重新繪製圖表
            if hasattr(self, 'canvas'):
                self.canvas.draw_idle()
                
            self.log(f"📊 已清除平均敏感度參考線，改用個別門敏感度標記")
                
        except Exception as e:
            print(f"清除平均參考線錯誤: {e}")
            self.log(f"⚠️ 清除平均參考線失敗: {e}")
    
    def draw_individual_sensitivity_markers(self):
        """在每個門的位置繪製個別敏感度標記 - 改進版本"""
        try:
            if not MATPLOTLIB_AVAILABLE or not hasattr(self, 'ax1') or not hasattr(self, 'ax2'):
                return
                
            # 清除舊的標記
            if hasattr(self, 'moving_sensitivity_markers'):
                for marker in self.moving_sensitivity_markers:
                    try:
                        marker.remove()
                    except:
                        pass
            if hasattr(self, 'still_sensitivity_markers'):
                for marker in self.still_sensitivity_markers:
                    try:
                        marker.remove()
                    except:
                        pass
            if hasattr(self, 'moving_sensitivity_texts'):
                for text in self.moving_sensitivity_texts:
                    try:
                        text.remove()
                    except:
                        pass
            if hasattr(self, 'still_sensitivity_texts'):
                for text in self.still_sensitivity_texts:
                    try:
                        text.remove()
                    except:
                        pass
            
            self.moving_sensitivity_markers = []
            self.still_sensitivity_markers = []
            self.moving_sensitivity_texts = []
            self.still_sensitivity_texts = []
            

            
            # 繪製移動目標各門敏感度標記 - 使用更明顯的標記
            markers_drawn = 0
            for i in range(14):
                if i < len(self.moving_gate_sensitivities):
                    sensitivity = self.moving_gate_sensitivities[i]
                    
                    # 繪製橫線標記
                    marker = self.ax1.plot([i-0.4, i+0.4], [sensitivity, sensitivity], 
                                         color='#ff6b6b', linewidth=3, alpha=0.9, 
                                         solid_capstyle='round')[0]
                    self.moving_sensitivity_markers.append(marker)
                    
                    # 添加數值標籤
                    text = self.ax1.text(i, sensitivity + 2, str(sensitivity), 
                                       ha='center', va='bottom', fontsize=8, 
                                       color='#ff6b6b', fontweight='bold',
                                       bbox=dict(boxstyle='round,pad=0.2', 
                                               facecolor='white', alpha=0.8, edgecolor='none'))
                    self.moving_sensitivity_texts.append(text)
                    markers_drawn += 1
            
            # 繪製靜止目標各門敏感度標記 - 使用更明顯的標記
            for i in range(14):
                if i < len(self.still_gate_sensitivities):
                    sensitivity = self.still_gate_sensitivities[i]
                    
                    # 繪製橫線標記
                    marker = self.ax2.plot([i-0.4, i+0.4], [sensitivity, sensitivity], 
                                         color='#ff6b6b', linewidth=3, alpha=0.9, 
                                         solid_capstyle='round')[0]
                    self.still_sensitivity_markers.append(marker)
                    
                    # 添加數值標籤
                    text = self.ax2.text(i, sensitivity + 2, str(sensitivity), 
                                       ha='center', va='bottom', fontsize=8, 
                                       color='#ff6b6b', fontweight='bold',
                                       bbox=dict(boxstyle='round,pad=0.2', 
                                               facecolor='white', alpha=0.8, edgecolor='none'))
                    self.still_sensitivity_texts.append(text)
            
            # 更新圖表標題，顯示個別門敏感度信息
            current_title1 = self.ax1.get_title()
            base_title1 = current_title1.split('\n')[0] if '\n' in current_title1 else current_title1.split('敏感度:')[0].split('🎯')[0]
            sens_str = ','.join([str(s) for s in self.moving_gate_sensitivities[:7]])
            self.ax1.set_title(f'{base_title1}\n🎯 門0-6敏感度: {sens_str}...', 
                              color='#4a9eff', fontsize=11, fontweight='bold')
            
            current_title2 = self.ax2.get_title()
            base_title2 = current_title2.split('\n')[0] if '\n' in current_title2 else current_title2.split('敏感度:')[0].split('🎯')[0]
            sens_str = ','.join([str(s) for s in self.still_gate_sensitivities[:7]])
            self.ax2.set_title(f'{base_title2}\n🎯 門0-6敏感度: {sens_str}...', 
                              color='#ef4444', fontsize=11, fontweight='bold')
            

                    
        except Exception as e:
            print(f"個別敏感度標記繪製錯誤: {e}")
            self.log(f"⚠️ 個別敏感度標記繪製失敗: {e}")
    
    def update_text_charts(self):
        """更新文字版圖表（matplotlib不可用時的備選方案）"""
        try:
            # 檢查是否有當前數據
            if not self.current_data:
                self.show_distance_trend()
                return
                
            if self.current_data.get('mode') != '工程模式':
                self.show_distance_trend()
                return
            
            # 工程模式 - 顯示門能量分布
            moving_energies = self.current_data.get('moving_gate_energies', [])
            still_energies = self.current_data.get('still_gate_energies', [])
            
            # 數據安全處理
            safe_moving = self.safe_convert_energies(moving_energies)
            safe_still = self.safe_convert_energies(still_energies)
            
            # 確保有14個門的數據
            safe_moving = (safe_moving + [0] * 14)[:14]
            safe_still = (safe_still + [0] * 14)[:14]
            
            # 獲取當前數據的其他字段
            timestamp = self.current_data.get('timestamp', datetime.now())
            light_value = self.current_data.get('light', 0)
            detect_dist = self.current_data.get('detect_dist', 0)
            
            # 創建移動目標圖表 - 使用個別門敏感度
            if safe_moving:
                moving_chart = self.create_individual_gate_chart("移動目標", safe_moving, self.moving_gate_sensitivities, 
                                                               14, 100, 12, "█", timestamp, light_value, detect_dist)
                self.moving_chart_text.delete(1.0, tk.END)
                self.moving_chart_text.insert(1.0, moving_chart)
            
            # 創建靜止目標圖表 - 使用個別門敏感度
            if safe_still:
                still_chart = self.create_individual_gate_chart("靜止目標", safe_still, self.still_gate_sensitivities,
                                                              14, 100, 12, "▓", timestamp, light_value, detect_dist)
                self.still_chart_text.delete(1.0, tk.END)
                self.still_chart_text.insert(1.0, still_chart)
                
        except Exception as e:
            print(f"文字圖表更新錯誤: {e}")
    
    def create_single_chart(self, target_type, energies, chart_width, max_energy, height, threshold_line, symbol, timestamp, light_value, detect_dist):
        """創建單一目標類型的能量圖表"""
        chart = f"""{target_type}能量分布圖 (工程模式)
更新時間: {timestamp.strftime('%H:%M:%S')}
光感值: {light_value}  檢測距離: {detect_dist} cm
{'='*50}

{target_type}能量 (門00-{chart_width-1:02d}):
{'-'*50}
"""
        
        # 繪製圖表
        for h in range(height, 0, -1):
            threshold = max_energy * h / height
            line = f"{threshold:3.0f} |"
            
            for i in range(chart_width):
                try:
                    energy = int(energies[i]) if i < len(energies) else 0
                    if energy >= threshold - (max_energy / height / 2):
                        line += f" {symbol}{symbol}"  # 三個字符寬度
                    else:
                        line += "   "  # 三個空格
                except (ValueError, TypeError, IndexError):
                    line += "   "  # 三個空格
            
            # 敏感度參考線
            if abs(threshold - threshold_line) < (max_energy / height / 2):
                line += f"  ← 敏感度參考線({threshold_line})"
            
            chart += line + "\n"
        
        # X軸標籤
        chart += "門號:"
        for i in range(chart_width):
            chart += f" {i:02d}"
        chart += "\n"
        
        # 顯示數值
        chart += f"{target_type}:"
        for i in range(chart_width):
            try:
                energy = int(energies[i]) if i < len(energies) else 0
                if energy > 99:
                    chart += " ##"
                else:
                    chart += f" {energy:02d}"
            except (ValueError, TypeError, IndexError):
                chart += " --"
        chart += "\n"
        
        # 詳細數值顯示
        chart += f"\n詳細能量值:\n"
        for i in range(min(chart_width, 14)):
            try:
                energy = int(energies[i]) if i < len(energies) else 0
                chart += f"門{i:02d}:{energy:3d} "
                if i == 6:  # 第7個門後換行
                    chart += "\n"
            except (ValueError, TypeError, IndexError):
                chart += f"門{i:02d}:--- "
        chart += "\n\n"
        
        # 距離對應說明
        chart += "距離對應:\n"
        for i in range(0, min(chart_width, 14), 2):
            distance_start = i * 0.75
            distance_end = (i + 1) * 0.75
            chart += f"門{i:02d}: {distance_start:.1f}m"
            if i + 1 < chart_width:
                chart += f"  門{i+1:02d}: {distance_end:.1f}m"
            chart += "\n"
        
        chart += f"\n提示: 能量值越高表示該距離區間的{target_type}信號越強"
        chart += f"\n當前最大檢測距離: {chart_width * 0.75:.1f}米"
        
        return chart
    
    def create_advanced_chart(self, target_type, energies, gate_sensitivities, chart_width, max_energy, height, avg_threshold, symbol, timestamp, light_value, detect_dist):
        """創建支援個別門敏感度的進階圖表"""
        chart = f"""{target_type}能量分布圖 (工程模式 - 個別門敏感度)
更新時間: {timestamp.strftime('%H:%M:%S')}
光感值: {light_value}  檢測距離: {detect_dist} cm
平均敏感度: {avg_threshold}
{'='*60}

{target_type}能量 (門00-{chart_width-1:02d}):
{'-'*60}
"""
        
        # 繪製圖表
        for h in range(height, 0, -1):
            threshold = max_energy * h / height
            line = f"{threshold:3.0f} |"
            
            for i in range(chart_width):
                try:
                    energy = int(energies[i]) if i < len(energies) else 0
                    gate_sensitivity = gate_sensitivities[i] if i < len(gate_sensitivities) else avg_threshold
                    
                    if energy >= threshold - (max_energy / height / 2):
                        # 根據是否超過個別門敏感度使用不同符號
                        if energy >= gate_sensitivity:
                            line += f" ◆◆"  # 超過個別門敏感度
                        else:
                            line += f" {symbol}{symbol}"  # 正常能量
                    else:
                        line += "   "  # 三個空格
                except (ValueError, TypeError, IndexError):
                    line += "   "  # 三個空格
            
            # 平均敏感度參考線
            if abs(threshold - avg_threshold) < (max_energy / height / 2):
                line += f"  ← 平均敏感度參考線({avg_threshold})"
            
            chart += line + "\n"
        
        # X軸標籤
        chart += "門號:"
        for i in range(chart_width):
            chart += f" {i:02d}"
        chart += "\n"
        
        # 顯示能量數值
        chart += f"能量:"
        for i in range(chart_width):
            try:
                energy = int(energies[i]) if i < len(energies) else 0
                if energy > 99:
                    chart += " ##"
                else:
                    chart += f" {energy:02d}"
            except (ValueError, TypeError, IndexError):
                chart += " --"
        chart += "\n"
        
        # 顯示個別門敏感度
        chart += f"敏感:"
        for i in range(chart_width):
            try:
                sensitivity = gate_sensitivities[i] if i < len(gate_sensitivities) else avg_threshold
                if sensitivity > 99:
                    chart += " ##"
                else:
                    chart += f" {sensitivity:02d}"
            except (ValueError, TypeError, IndexError):
                chart += " --"
        chart += "\n"
        
        # 狀態指示
        chart += f"狀態:"
        for i in range(chart_width):
            try:
                energy = int(energies[i]) if i < len(energies) else 0
                sensitivity = gate_sensitivities[i] if i < len(gate_sensitivities) else avg_threshold
                if energy >= sensitivity:
                    chart += " ◆◆"  # 超過敏感度
                else:
                    chart += " ··"  # 未超過敏感度
            except (ValueError, TypeError, IndexError):
                chart += " --"
        chart += "\n\n"
        
        # 詳細說明
        chart += f"詳細分析:\n"
        triggered_gates = []
        for i in range(min(chart_width, 14)):
            try:
                energy = int(energies[i]) if i < len(energies) else 0
                sensitivity = gate_sensitivities[i] if i < len(gate_sensitivities) else avg_threshold
                status = "觸發" if energy >= sensitivity else "正常"
                chart += f"門{i:02d}: 能量{energy:3d} / 敏感度{sensitivity:3d} = {status}\n"
                if energy >= sensitivity:
                    triggered_gates.append(i)
            except (ValueError, TypeError, IndexError):
                chart += f"門{i:02d}: 數據錯誤\n"
        
        if triggered_gates:
            distances = [f"{gate*0.75:.1f}m" for gate in triggered_gates]
            chart += f"\n🚨 觸發的門: {triggered_gates} (距離: {', '.join(distances)})\n"
        else:
            chart += f"\n✅ 所有門均未觸發敏感度閾值\n"
        
        chart += f"\n圖例說明:\n"
        chart += f"  {symbol}{symbol} = 正常能量  ◆◆ = 超過敏感度  ·· = 未觸發\n"
        chart += f"  平均敏感度: {avg_threshold}  個別敏感度: 如上表所示"
        
        return chart

    def create_individual_gate_chart(self, target_type, energies, gate_sensitivities, chart_width, max_energy, height, symbol, timestamp, light_value, detect_dist):
        """創建使用個別門敏感度的圖表 - 不使用平均敏感度"""
        chart = f"""{target_type}能量分布圖 (工程模式 - 個別門敏感度)
更新時間: {timestamp.strftime('%H:%M:%S')}
光感值: {light_value}  檢測距離: {detect_dist} cm
🎯 使用個別門敏感度設定
{'='*60}

{target_type}能量 (門00-{chart_width-1:02d}):
{'-'*60}
"""
        
        # 繪製圖表
        for h in range(height, 0, -1):
            threshold = max_energy * h / height
            line = f"{threshold:3.0f} |"
            
            for i in range(chart_width):
                try:
                    energy = int(energies[i]) if i < len(energies) else 0
                    gate_sensitivity = gate_sensitivities[i] if i < len(gate_sensitivities) else 50
                    
                    if energy >= threshold - (max_energy / height / 2):
                        # 根據是否超過個別門敏感度使用不同符號
                        if energy >= gate_sensitivity:
                            line += f" ◆◆"  # 超過個別門敏感度
                        else:
                            line += f" {symbol}{symbol}"  # 正常能量
                    else:
                        line += "   "  # 三個空格
                except (ValueError, TypeError, IndexError):
                    line += "   "  # 三個空格
            
            chart += line + "\n"
        
        # X軸標籤
        chart += "門號:"
        for i in range(chart_width):
            chart += f" {i:02d}"
        chart += "\n"
        
        # 顯示能量數值
        chart += f"能量:"
        for i in range(chart_width):
            try:
                energy = int(energies[i]) if i < len(energies) else 0
                if energy > 99:
                    chart += " ##"
                else:
                    chart += f" {energy:02d}"
            except (ValueError, TypeError, IndexError):
                chart += " --"
        chart += "\n"
        
        # 顯示個別門敏感度
        chart += f"敏感:"
        for i in range(chart_width):
            try:
                sensitivity = gate_sensitivities[i] if i < len(gate_sensitivities) else 50
                if sensitivity > 99:
                    chart += " ##"
                else:
                    chart += f" {sensitivity:02d}"
            except (ValueError, TypeError, IndexError):
                chart += " --"
        chart += "\n"
        
        # 狀態指示
        chart += f"狀態:"
        for i in range(chart_width):
            try:
                energy = int(energies[i]) if i < len(energies) else 0
                sensitivity = gate_sensitivities[i] if i < len(gate_sensitivities) else 50
                if energy >= sensitivity:
                    chart += " ◆◆"  # 超過敏感度
                else:
                    chart += " ··"  # 未超過敏感度
            except (ValueError, TypeError, IndexError):
                chart += " --"
        chart += "\n\n"
        
        # 詳細分析
        chart += f"📊 各門詳細狀態:\n"
        triggered_gates = []
        for i in range(min(chart_width, 14)):
            try:
                energy = int(energies[i]) if i < len(energies) else 0
                sensitivity = gate_sensitivities[i] if i < len(gate_sensitivities) else 50
                status = "🔴觸發" if energy >= sensitivity else "⚪正常"
                distance = i * 0.75
                chart += f"門{i:02d}({distance:.1f}m): 能量{energy:3d}/敏感度{sensitivity:3d} = {status}\n"
                if energy >= sensitivity:
                    triggered_gates.append(i)
            except (ValueError, TypeError, IndexError):
                chart += f"門{i:02d}: 數據錯誤\n"
        
        if triggered_gates:
            distances = [f"{gate*0.75:.1f}m" for gate in triggered_gates]
            chart += f"\n🚨 觸發的門: {triggered_gates} (距離: {', '.join(distances)})\n"
        else:
            chart += f"\n✅ 所有門均未觸發個別敏感度閾值\n"
        
        chart += f"\n📋 圖例說明:\n"
        chart += f"  {symbol}{symbol} = 正常能量  ◆◆ = 超過個別門敏感度  ·· = 未觸發\n"
        chart += f"  🎯 每個門都有獨立的敏感度設定，不使用平均值"
        
        return chart
    
    def show_distance_trend(self):
        """顯示距離趨勢圖 (正常模式)"""
        if len(self.data_history['detection_distance']) < 5:
            chart = """門能量分布圖 (等待工程模式數據...)

請執行以下步驟查看門能量分布:
1. 點擊「🔧 開啟工程模式」
2. 點擊「🚀 啟動數據輸出」  
3. 系統將顯示各門的詳細能量分布

正常模式下顯示距離趨勢:
"""
            self.chart_text.delete(1.0, tk.END)
            self.chart_text.insert(1.0, chart)
            return
        
        # 獲取最近30個數據點
        data = list(self.data_history['detection_distance'])[-30:]
        if not data or max(data) == 0:
            return
        
        max_val = max(data)
        min_val = min([d for d in data if d > 0]) if any(d > 0 for d in data) else 0
        height = 15
        
        chart = f"""距離趨勢圖 (正常模式 - 最近{len(data)}個數據點)
最大值: {max_val} cm  最小值: {min_val} cm
{'='*60}
"""
        
        # 繪製圖表
        for h in range(height, 0, -1):
            threshold = min_val + (max_val - min_val) * h / height if max_val > min_val else min_val
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
        chart += "\n█ = 檢測到目標  ░ = 低於閾值  空白 = 無目標\n"
        chart += "提示: 開啟工程模式可查看詳細門能量分布"
        
        # 正常模式下，兩個視窗都顯示相同內容
        self.moving_chart_text.delete(1.0, tk.END)
        self.moving_chart_text.insert(1.0, chart)
        
        self.still_chart_text.delete(1.0, tk.END)
        self.still_chart_text.insert(1.0, chart)
    
    def add_text(self, widget, text):
        """添加文字到文本框 - 優化版本"""
        try:
            widget.insert(tk.END, text)
            widget.see(tk.END)
            
            # 更積極的行數限制，避免記憶體問題
            lines = widget.get("1.0", tk.END).split('\n')
            if len(lines) > 100:  # 減少最大行數
                widget.delete("1.0", f"{len(lines)-50}.0")  # 保留最近50行
        except Exception as e:
            # 如果文本框操作失敗，記錄到控制台
            print(f"文本框操作錯誤: {e}")
    
    def toggle_connection(self):
        """切換連接狀態"""
        if not self.is_connected:
            # 檢查 serial 模組是否可用
            if serial is None:
                messagebox.showerror("模組錯誤", "PySerial 模組未正確導入\n請安裝: pip install pyserial")
                return
                
            try:
                self.port_name = self.port_var.get().strip()
                self.baud_rate = int(self.baud_var.get())
                
                self.log(f"🔌 嘗試連接 {self.port_name} (波特率: {self.baud_rate})")
                
                # 先檢查串列埠是否存在
                if not self.check_port_exists(self.port_name):
                    available_ports = self.get_available_ports()
                    error_msg = f"串列埠 {self.port_name} 不存在\n\n可用的串列埠:\n"
                    if available_ports:
                        for port, desc in available_ports:
                            error_msg += f"• {port} - {desc}\n"
                    else:
                        error_msg += "• 未找到任何串列埠設備"
                    
                    self.log(f"❌ 串列埠不存在: {self.port_name}")
                    messagebox.showerror("串列埠錯誤", error_msg)
                    return
                
                # 嘗試連接
                self.log(f"🔧 正在開啟串列埠...")
                self.serial_port = Serial(
                    port=self.port_name, 
                    baudrate=self.baud_rate, 
                    timeout=1,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE
                )
                
                # 檢查連接是否真的成功
                if self.serial_port and self.serial_port.is_open:
                    self.is_connected = True
                    self.is_monitoring = False  # 重置監控狀態
                    self.connect_btn.config(text="🔌 斷開")
                    self.monitor_btn.config(text="▶️ 開始監控")  # 重置監控按鈕
                    self.status_label.config(text="🟢 已連接", fg=self.colors['accent_green'])
                    self.config_label.config(text="📝 正常模式")
                    self.log(f"✅ 成功連接 {self.port_name} ({self.baud_rate})")
                    
                    # 測試串列埠是否可讀寫
                    try:
                        # 清空緩衝區
                        self.serial_port.reset_input_buffer()
                        self.serial_port.reset_output_buffer()
                        self.log(f"🧹 已清空串列埠緩衝區")
                    except Exception as e:
                        self.log(f"⚠️ 清空緩衝區失敗: {e}")
                else:
                    self.log(f"❌ 串列埠開啟失敗")
                    messagebox.showerror("連接錯誤", "串列埠開啟失敗")
                    
            except SerialException as e:
                self.log(f"❌ 串列埠錯誤: {e}")
                error_details = str(e)
                if "Permission denied" in error_details:
                    suggestion = f"權限被拒絕，請嘗試執行:\nsudo chmod 666 {self.port_name}"
                elif "Device or resource busy" in error_details:
                    suggestion = "設備被佔用，請檢查是否有其他程序正在使用此串列埠"
                elif "No such file or directory" in error_details:
                    suggestion = "設備不存在，請檢查設備是否正確連接"
                else:
                    suggestion = "請檢查設備連接和驅動程序"
                    
                messagebox.showerror("串列埠錯誤", 
                    f"無法開啟串列埠 {self.port_name}\n\n錯誤詳情: {e}\n\n建議解決方案:\n{suggestion}")
                    
            except ValueError as e:
                self.log(f"❌ 參數錯誤: {e}")
                messagebox.showerror("參數錯誤", f"波特率設定錯誤: {e}")
                
            except Exception as e:
                self.log(f"❌ 未知錯誤: {e}")
                import traceback
                traceback.print_exc()  # 輸出完整錯誤信息到控制台
                messagebox.showerror("連接錯誤", f"連接失敗\n\n錯誤詳情: {e}\n\n請檢查設備連接")
        else:
            # 完全斷開連接
            self.is_monitoring = False
            if self.serial_port and self.serial_port.is_open:
                try:
                    self.serial_port.close()
                except:
                    pass
            self.serial_port = None
            self.is_connected = False
            
            # 重置UI狀態
            self.connect_btn.config(text="🔌 連接")
            self.monitor_btn.config(text="▶️ 開始監控")
            self.status_label.config(text="🔴 已斷開", fg=self.colors['accent_red'])
            self.config_label.config(text="📝 正常模式", fg=self.colors['fg_secondary'])
            
            # 重置狀態變量
            self.is_config_mode = False
            
            # 清理數據緩衝區
            self.raw_buffer.clear()
            while not self.data_queue.empty():
                try:
                    self.data_queue.get_nowait()
                except:
                    break
                    
            self.log("🔌 已斷開連接")
    
    def toggle_monitoring(self):
        """切換監控狀態"""
        if not self.is_connected:
            messagebox.showwarning("警告", "請先連接串列埠")
            return
        
        self.is_monitoring = not self.is_monitoring
        if self.is_monitoring:
            self.monitor_btn.config(text="⏹️ 停止監控")
            self.log("🔍 開始監控")
        else:
            self.monitor_btn.config(text="▶️ 開始監控")
            self.log("⏹️ 停止監控")
    
    def send_command(self, hex_string):
        """發送命令"""
        if not self.is_connected:
            messagebox.showwarning("警告", "請先連接串列埠")
            return
        
        # 檢查命令間隔，避免發送過快 - 配置模式下減少間隔
        current_time = time.time()
        min_interval = 0.1 if self.is_config_mode else 0.2  # 配置模式下0.1秒間隔
        if current_time - self.last_command_time < min_interval:
            time.sleep(min_interval - (current_time - self.last_command_time))
        
        try:
            cmd = bytes.fromhex(hex_string.replace(" ", ""))
            self.serial_port.write(cmd)
            self.serial_port.flush()
            
            # 設置命令等待狀態
            self.last_command_time = time.time()
            self.waiting_for_response = True
            self.last_command_sent = hex_string
            
            self.log(f"📤 {hex_string}")
            
            # 特殊命令處理 - 基於官方LD2412庫
            if hex_string == "FD FC FB FA 04 00 FF 00 01 00 04 03 02 01":
                # 進入配置模式 (CMD_ENABLE_CONF)
                self.is_config_mode = True
                self.config_label.config(text="⚙️ 配置模式", fg=self.colors['accent_yellow'])
                
            elif hex_string == "FD FC FB FA 02 00 FE 00 04 03 02 01":
                # 退出配置模式 (CMD_DISABLE_CONF)
                self.is_config_mode = False
                self.config_label.config(text="📝 正常模式", fg=self.colors['fg_secondary'])
                
            elif hex_string == "FD FC FB FA 02 00 12 00 04 03 02 01":
                # 查詢命令 (CMD_QUERY)
                if not self.is_monitoring:
                    self.log("💡 建議先開始監控以查看查詢結果")
                    
            elif hex_string == "FD FC FB FA 02 00 A3 00 04 03 02 01":
                # 重啟模組 (CMD_RESTART)
                self.is_config_mode = False
                self.config_label.config(text="🔄 重啟中...", fg=self.colors['accent_yellow'])
                
            elif hex_string == "FD FC FB FA 02 00 A2 00 04 03 02 01":
                # 恢復出廠設定 (CMD_RESET)
                self.is_config_mode = False
                self.config_label.config(text="🏭 出廠設定", fg=self.colors['accent_red'])
                    
            elif hex_string == "FD FC FB FA 02 00 62 00 04 03 02 01":
                # 開啟工程模式 (CMD_ENABLE_ENG)
                self.log("🔧 工程模式指令已發送")
                
            elif hex_string == "FD FC FB FA 02 00 63 00 04 03 02 01":
                # 關閉工程模式 (CMD_DISABLE_ENG)
                self.log("🔧 正常模式指令已發送")
                
            elif hex_string.startswith("FD FC FB FA 08 00 01 00"):
                # 距離分辨率設定 (CMD_SET_DISTANCE_RESOLUTION)
                if not self.is_config_mode:
                    self.log("⚠️ 建議先進入配置模式")
                    
            elif hex_string.startswith("FD FC FB FA 04 00 A1 00"):
                # 波特率設定 (CMD_SET_BAUD_RATE)
                if not self.is_config_mode:
                    self.log("⚠️ 建議先進入配置模式")
                self.log("📡 波特率變更後需要重啟模組")
                
            elif hex_string.startswith("FD FC FB FA 04 00 A4 00"):
                # 藍牙控制 (CMD_BLUETOOTH)
                if not self.is_config_mode:
                    self.log("⚠️ 建議先進入配置模式")
                    
            elif hex_string == "FD FC FB FA 02 00 0B 00 04 03 02 01":
                # 動態背景校正 (CMD_DYNAMIC_BACKGROUND_CORRECTION)
                if not self.is_config_mode:
                    self.log("⚠️ 建議先進入配置模式")
                self.log("🎯 動態背景校正需要約2分鐘完成")
                
            elif hex_string in ["FD FC FB FA 02 00 13 00 04 03 02 01", 
                               "FD FC FB FA 02 00 14 00 04 03 02 01"]:
                # 門敏感度查詢 (CMD_QUERY_MOTION_GATE_SENS, CMD_QUERY_STATIC_GATE_SENS)
                if not self.is_config_mode:
                    self.log("⚠️ 建議先進入配置模式")
                    
        except Exception as e:
            self.waiting_for_response = False
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
        self.detailed_text.delete(1.0, tk.END)  # 清除詳細解析分頁
        self.moving_chart_text.delete(1.0, tk.END)
        self.still_chart_text.delete(1.0, tk.END)
        
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
            'last_update': time.time()
        }
        
        self.current_data = None
    
    def quick_start(self):
        """快速開始 - 一鍵開啟監控並啟動數據輸出"""
        if not self.is_connected:
            messagebox.showwarning("警告", "請先連接串列埠")
            return
        
        # 開始監控
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_btn.config(text="⏹️ 停止監控")
        
        # 發送啟動數據輸出命令
        self.send_command("FD FC FB FA 02 00 12 00 04 03 02 01")
    
    def log(self, message):
        """記錄日誌"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}\n"
        self.add_text(self.log_text, log_entry)
    
    def check_port_exists(self, port_name):
        """檢查串列埠是否存在"""
        try:
            import os
            return os.path.exists(port_name)
        except:
            return False
    
    def get_available_ports(self):
        """獲取可用的串列埠列表"""
        try:
            import serial.tools.list_ports
            ports = []
            for port, desc, hwid in serial.tools.list_ports.comports():
                ports.append((port, desc))
            return ports
        except ImportError:
            # 如果沒有安裝 pyserial 的 tools，手動檢查常見埠
            import glob
            import os
            possible_ports = []
            
            # macOS 常見串列埠
            patterns = ['/dev/cu.*', '/dev/tty.usb*', '/dev/tty.wchusbserial*']
            for pattern in patterns:
                possible_ports.extend(glob.glob(pattern))
            
            # 過濾存在的埠
            ports = []
            for port in possible_ports:
                if os.path.exists(port):
                    ports.append((port, "串列埠設備"))
            
            return ports
        except Exception as e:
            print(f"獲取串列埠列表失敗: {e}")
            return []
    
    def update_port_list(self):
        """更新串列埠下拉選單"""
        try:
            available_ports = self.get_available_ports()
            port_list = [port for port, desc in available_ports]
            
            if hasattr(self, 'port_combo'):
                self.port_combo['values'] = port_list
                # 如果當前設定的埠不在列表中，但存在，則添加到列表
                current_port = self.port_var.get()
                if current_port and current_port not in port_list and self.check_port_exists(current_port):
                    port_list.append(current_port)
                    self.port_combo['values'] = port_list
        except Exception as e:
            print(f"更新串列埠列表失敗: {e}")
    
    def refresh_ports(self):
        """刷新串列埠列表"""
        available_ports = self.get_available_ports()
        if available_ports:
            self.log("🔍 可用串列埠:")
            for port, desc in available_ports:
                self.log(f"  • {port} - {desc}")
        else:
            self.log("❌ 未找到任何串列埠設備")
        
        # 同時更新下拉選單
        self.update_port_list()
    
    def auto_disconnect(self):
        """自動斷開連接"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
        except:
            pass
        
        self.serial_port = None
        self.is_connected = False
        self.is_monitoring = False
        self.connect_btn.config(text="🔌 連接")
        self.monitor_btn.config(text="▶️ 開始監控")
        self.status_label.config(text="🔴 已斷開", fg=self.colors['accent_red'])
        self.config_label.config(text="📝 正常模式", fg=self.colors['fg_secondary'])
        
        # 重置狀態變量
        self.is_config_mode = False
        
        # 清理數據緩衝區
        self.raw_buffer.clear()
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except:
                break
    
    def parse_command_response(self, frame):
        """解析命令回應幀 - 基於協議文檔實現"""
        if len(frame) < 8:  # 最小命令回應幀長度
            return
        
        # 標記收到回應
        if self.waiting_for_response:
            self.waiting_for_response = False
        
        # 解析命令回應結構 - 根據協議文檔重新分析
        data_length = frame[4] | (frame[5] << 8)  # 數據長度（小端序）
        command_code = frame[6] | (frame[7] << 8)  # 命令碼（小端序）
        
        # 調試信息
        frame_hex = ' '.join([f'{b:02X}' for b in frame])
        print(f"解析命令回應: 長度={len(frame)}, 數據長度={data_length}")
        print(f"完整幀: {frame_hex}")
        print(f"命令碼: 0x{command_code:04X}")
        
        # 檢查ACK狀態（前兩個字節通常是 00 00 表示成功）
        success = True
        if len(frame) >= 10:
            ack_status = frame[8] | (frame[9] << 8)
            success = (ack_status == 0x0000)
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # 立即輸出基本回應信息到日誌
        self.log(f"📥 命令回應: 0x{command_code:04X}, 長度={len(frame)}, 數據長度={data_length}")
        
        # 狀態指示符
        status_icon = "✅" if success else "❌"
        status_text = "成功" if success else "失敗"
        
        # 根據命令碼解析不同類型的回應
        if command_code == 0x01A0:  # CMD_VERSION (回應碼)
            if len(frame) >= 18 and success:
                # 協議文檔：韌體類型(2字節) + 主版本號(2字節) + 次版本號(4字節)
                version_data = frame[10:]  # 跳過ACK狀態
                if len(version_data) >= 8:
                    firmware_type = version_data[0] | (version_data[1] << 8)
                    major_version = version_data[2] | (version_data[3] << 8)
                    minor_version = int.from_bytes(version_data[4:8], 'little')
                    
                    version_str = f"韌體類型: 0x{firmware_type:04X}, 主版本: {major_version >> 8}.{major_version & 0xFF}, 次版本: {minor_version}"
                    full_version = f"V{major_version >> 8}.{major_version & 0xFF}.{minor_version}"
                    self.log(f"{status_icon} 版本查詢{status_text}: {version_str}")
                    self.log(f"📋 完整版本號: {full_version}")
                else:
                    version_hex = ' '.join([f'{b:02X}' for b in version_data])
                    self.log(f"{status_icon} 版本查詢{status_text}: 原始數據={version_hex}")
            else:
                self.log(f"{status_icon} 版本查詢{status_text}")
                
        elif command_code == 0x0112:  # CMD_QUERY - 查詢參數 (回應碼)
            if len(frame) >= 15 and success:
                # 協議文檔：最小距離門(1字節) + 最大距離門(1字節) + 無人持續時間(2字節) + OUT腳輸出極性(1字節)
                param_data = frame[10:]  # 跳過ACK狀態
                if len(param_data) >= 5:
                    min_gate = param_data[0]
                    max_gate = param_data[1]
                    timeout = param_data[2] | (param_data[3] << 8)
                    out_polarity = param_data[4]
                    out_desc = "有人輸出高電平" if out_polarity == 0 else "有人輸出低電平"
                    
                    self.log(f"{status_icon} 參數查詢{status_text}:")
                    self.log(f"  📏 最小距離門: {min_gate} ({min_gate * 0.75:.1f}m)")
                    self.log(f"  📏 最大距離門: {max_gate} ({max_gate * 0.75:.1f}m)")
                    self.log(f"  ⏱️ 無人持續時間: {timeout}秒")
                    self.log(f"  🔌 OUT腳極性: {out_desc}")
                else:
                    data_hex = ' '.join([f'{b:02X}' for b in param_data])
                    self.log(f"{status_icon} 參數查詢{status_text}: 原始數據={data_hex}")
            else:
                self.log(f"{status_icon} 參數查詢{status_text}")
                
        elif command_code == 0x01FF:  # CMD_ENABLE_CONF (回應碼)
            if success:
                config_data = frame[10:]  # 跳過ACK狀態
                if len(config_data) >= 2:
                    protocol_version = config_data[0] | (config_data[1] << 8)
                    self.log(f"{status_icon} 進入配置模式{status_text}: 協議版本 v{protocol_version >> 8}.{protocol_version & 0xFF}")
                else:
                    self.log(f"{status_icon} 進入配置模式{status_text}")
            else:
                self.log(f"{status_icon} 進入配置模式{status_text}")
                
        elif command_code == 0x01FE:  # CMD_DISABLE_CONF (回應碼)
            self.log(f"{status_icon} 退出配置模式{status_text}")
            
        elif command_code == 0x0062:  # CMD_ENABLE_ENG
            self.log(f"{status_icon} 開啟工程模式{status_text}")
            
        elif command_code == 0x0063:  # CMD_DISABLE_ENG
            self.log(f"{status_icon} 關閉工程模式{status_text}")
            
        elif command_code == 0x00A3:  # CMD_RESTART
            self.log(f"{status_icon} 模組重啟{status_text}")
            
        elif command_code == 0x00A2:  # CMD_RESET
            self.log(f"{status_icon} 出廠設定恢復{status_text}")
            
        elif command_code == 0x0001:  # CMD_SET_DISTANCE_RESOLUTION
            self.log(f"{status_icon} 距離分辨率設定{status_text} (需要重啟模組生效)")
            
        elif command_code == 0x0111:  # CMD_QUERY_DISTANCE_RESOLUTION (回應碼)
            if len(frame) >= 16 and success:
                # 協議文檔：分辨率值(1字節) + 保留(5字節)
                resolution_data = frame[10:]  # 跳過ACK狀態
                if len(resolution_data) >= 6:
                    resolution_code = resolution_data[0]
                    resolution_map = {
                        0x00: "75cm/距離門 (12米範圍)",
                        0x01: "50cm/距離門 (8米範圍)",
                        0x03: "20cm/距離門 (3.2米範圍)"
                    }
                    resolution = resolution_map.get(resolution_code, f"未知分辨率 0x{resolution_code:02X}")
                    self.log(f"{status_icon} 距離分辨率查詢{status_text}: {resolution}")
                else:
                    data_hex = ' '.join([f'{b:02X}' for b in resolution_data])
                    self.log(f"{status_icon} 距離分辨率查詢{status_text}: 原始數據={data_hex}")
            else:
                self.log(f"{status_icon} 距離分辨率查詢{status_text}")
                
        elif command_code == 0x00A1:  # CMD_SET_BAUD_RATE
            self.log(f"{status_icon} 波特率設定{status_text} (需要重啟模組生效)")
            
        elif command_code == 0x00A4:  # CMD_BLUETOOTH
            if success:
                bt_data = frame[10:] if len(frame) > 10 else []
                if bt_data:
                    enable_status = bt_data[0] if len(bt_data) > 0 else 0
                    bt_status = "開啟" if enable_status == 0x01 else "關閉"
                    self.log(f"{status_icon} 藍牙設定{status_text}: {bt_status}")
                else:
                    self.log(f"{status_icon} 藍牙設定{status_text}")
            else:
                self.log(f"{status_icon} 藍牙設定{status_text}")
                
        elif command_code == 0x01A5:  # CMD_MAC (回應碼)
            if len(frame) >= 16 and success:
                # 協議文檔：6字節MAC地址
                mac_data = frame[10:]  # 跳過ACK狀態
                if len(mac_data) >= 6:
                    mac_str = ':'.join([f'{b:02X}' for b in mac_data[:6]])
                    self.log(f"{status_icon} MAC查詢{status_text}: {mac_str}")
                else:
                    mac_hex = ' '.join([f'{b:02X}' for b in mac_data])
                    self.log(f"{status_icon} MAC查詢{status_text}: 原始數據={mac_hex}")
            else:
                self.log(f"{status_icon} MAC查詢{status_text}")
                
        elif command_code == 0x000B:  # CMD_DYNAMIC_BACKGROUND_CORRECTION
            self.log(f"{status_icon} 動態背景校正{status_text} (需約2分鐘完成)")
            
        elif command_code == 0x011B:  # CMD_QUEY_DYNAMIC_BACKGROUND_CORRECTION (回應碼)
            if len(frame) >= 12 and success:
                # 協議文檔：狀態數據(2字節)
                bg_data = frame[10:]  # 跳過ACK狀態
                if len(bg_data) >= 2:
                    bg_status = bg_data[0] | (bg_data[1] << 8)
                    bg_status_text = "正在執行動態背景校正中" if bg_status == 0x0001 else "未在執行動態背景校正"
                    self.log(f"{status_icon} 背景校正狀態查詢{status_text}: {bg_status_text}")
                else:
                    self.log(f"{status_icon} 背景校正狀態查詢{status_text}")
            else:
                self.log(f"{status_icon} 背景校正狀態查詢{status_text}")
                
        elif command_code == 0x0113:  # CMD_QUERY_MOTION_GATE_SENS (回應碼)
            if len(frame) >= 20 and success:
                # 根據協議文檔重新解析
                # 跳過幀頭(4) + 長度(2) + 命令(2) + 狀態(1) = 9字節，然後是回應數據
                response_data = frame[9:]  # 從第9字節開始是回應數據
                
                # 協議格式: ACK狀態(2字節) + 門0敏感度(1字節) + 門1-12敏感度
                if len(response_data) >= 3:
                    ack_status = response_data[0] | (response_data[1] << 8)
                    gate0_sens = response_data[2]  # 門0敏感度
                    
                    # 提取門1-12敏感度數據（從第3字節開始，排除幀尾4字節）
                    remaining_sens_data = response_data[3:-4]  # 排除幀尾 04 03 02 01
                    
                    # 組合所有敏感度值：門0 + 門1-12
                    sens_values = [int(gate0_sens)]  # 先加入門0
                    for i in range(len(remaining_sens_data)):
                        sens_val = int(remaining_sens_data[i])
                        sens_values.append(sens_val)
                    
                    available_gates = len(sens_values)
                    
                    # 如果不足14門，用預設值補齊
                    while len(sens_values) < 14:
                        sens_values.append(50)  # 預設敏感度50
                    
                    # 格式化顯示
                    sens_str = ' '.join([f'{v:3d}' for v in sens_values])
                    self.log(f"{status_icon} 移動門敏感度查詢{status_text}")
                    self.log(f"📊 移動門敏感度(ACK:{ack_status:04X}): {sens_str}")
                    self.log(f"📊 實際收到{available_gates}門敏感度，已補齊至14門")
                    
                    # 立即更新移動目標敏感度數組
                    self.moving_gate_sensitivities = sens_values[:14]  # 確保恰好14個
                    
                    self.log(f"✅ 移動敏感度已更新: 個別門敏感度設定完成")
                    
                    # 立即觸發圖表更新 - 只更新個別門標記，不使用平均參考線
                    if MATPLOTLIB_AVAILABLE and hasattr(self, 'ax1'):
                        self.root.after(50, self.draw_individual_sensitivity_markers)
                        self.root.after(150, lambda: (
                            self.canvas.draw() if hasattr(self, 'canvas') else None,
                            self.log("🔄 移動門個別敏感度標記已更新")
                        ))
                else:
                    self.log(f"❌ 移動敏感度回應數據長度不足: {len(response_data)} < 3")
            else:
                self.log(f"{status_icon} 移動門敏感度查詢{status_text}: 幀長度不足或狀態失敗")

        elif command_code == 0x0114:  # CMD_QUERY_STATIC_GATE_SENS (回應碼)
            if len(frame) >= 20 and success:
                # 重新分析幀結構
                # 幀結構: 幀頭(4) + 長度(2) + 命令(2) + 狀態(1) + ACK(2) + 敏感度數據(14) + 幀尾(4)
                # 敏感度數據位置: 從第11字節開始
                
                # 調試: 顯示完整幀信息
                frame_hex = ' '.join([f'{b:02X}' for b in frame])
                self.log(f"🔍 完整幀: {frame_hex}")
                
                # 提取ACK狀態（位置9-10）
                ack_status = frame[9] | (frame[10] << 8)
                
                # 提取14門敏感度數據（位置11-24）
                sens_data_start = 11
                sens_data_end = 25  # 不包含
                
                sens_values = []
                for i in range(sens_data_start, min(sens_data_end, len(frame)-4)):  # 排除幀尾
                    sens_values.append(int(frame[i]))
                
                available_gates = len(sens_values)
                
                # 調試信息
                self.log(f"🔍 ACK狀態: {ack_status:04X}")
                self.log(f"🔍 敏感度數據位置 {sens_data_start}-{sens_data_end-1}")
                sens_hex = ' '.join([f'{frame[i]:02X}' for i in range(sens_data_start, min(sens_data_end, len(frame)-4))])
                self.log(f"🔍 敏感度原始數據: {sens_hex}")
                self.log(f"🔍 解析後敏感度值: {sens_values}")
                
                # 如果不足14門，用預設值補齊
                while len(sens_values) < 14:
                    sens_values.append(25)  # 預設敏感度25
                    
                    # 格式化顯示
                    sens_str = ' '.join([f'{v:3d}' for v in sens_values])
                    self.log(f"{status_icon} 靜止門敏感度查詢{status_text}")
                    self.log(f"📊 靜止門敏感度(ACK:{ack_status:04X}): {sens_str}")
                    self.log(f"📊 實際收到{available_gates}門敏感度，已補齊至14門")
                    
                    # 立即更新靜止目標敏感度數組
                    self.still_gate_sensitivities = sens_values[:14]  # 確保恰好14個
                    
                    self.log(f"✅ 靜止敏感度已更新: 個別門敏感度設定完成")
                    
                    # 立即觸發圖表更新 - 只更新個別門標記，不使用平均參考線
                    if MATPLOTLIB_AVAILABLE and hasattr(self, 'ax2'):
                        self.root.after(50, self.draw_individual_sensitivity_markers)
                        self.root.after(150, lambda: (
                            self.canvas.draw() if hasattr(self, 'canvas') else None,
                            self.log("🔄 靜止門個別敏感度標記已更新")
                        ))
                else:
                    self.log(f"❌ 靜止敏感度回應數據長度不足: {len(response_data)} < 3")
            else:
                self.log(f"{status_icon} 靜止門敏感度查詢{status_text}: 幀長度不足或狀態失敗")
        
        elif command_code == 0x000C:  # CMD_SET_LIGHT_CONTROL - 光感輔助控制設定
            self.log(f"{status_icon} 光感輔助控制設定{status_text}")
        
        elif command_code == 0x011C:  # CMD_QUERY_LIGHT_CONTROL - 光感輔助控制查詢 (回應碼)
            if len(frame) >= 12 and success:
                # 協議文檔：控制模式(1字節) + 光感閾值(1字節)
                light_data = frame[10:]  # 跳過ACK狀態
                if len(light_data) >= 2:
                    control_mode = light_data[0]
                    light_threshold = light_data[1]
                    
                    mode_description = {
                        0x00: "關閉光感輔助控制功能",
                        0x01: "光感值小於閾值時輔助控制條件滿足",
                        0x02: "光感值大於閾值時輔助控制條件滿足"
                    }
                    
                    mode_text = mode_description.get(control_mode, f"未知模式 0x{control_mode:02X}")
                    
                    self.log(f"{status_icon} 光感輔助控制查詢{status_text}:")
                    self.log(f"  💡 控制模式: {mode_text}")
                    self.log(f"  💡 光感閾值: {light_threshold} (0-255)")
                else:
                    data_hex = ' '.join([f'{b:02X}' for b in light_data])
                    self.log(f"{status_icon} 光感輔助控制查詢{status_text}: 原始數據={data_hex}")
            else:
                self.log(f"{status_icon} 光感輔助控制查詢{status_text}")
                
        else:
            # 通用回應顯示
            response_data = frame[8:] if len(frame) > 8 else []
            if response_data:
                response_str = ' '.join([f'{b:02X}' for b in response_data])
                self.log(f"{status_icon} 命令[0x{command_code:04X}]{status_text}: {response_str}")
            else:
                self.log(f"{status_icon} 命令[0x{command_code:04X}]{status_text}")
        
        # 詳細解析結果（顯示重要回應的詳細信息）
        important_commands = [0x01A0, 0x0112, 0x0111, 0x01A5, 0x0113, 0x0114, 0x011C, 0x011B]
        if command_code in important_commands or not success:
            result = f"""[{timestamp}] 命令回應幀 - 命令碼: 0x{command_code:04X}
幀長度: {len(frame)} 字節  數據長度: {data_length}  狀態: {status_text}
原始幀: {' '.join([f'{b:02X}' for b in frame])}
回應數據: {' '.join([f'{b:02X}' for b in frame[8:]]) if len(frame) > 8 else '無'}
{"="*50}
"""
            self.add_text(self.detailed_text, result)
    
    # 組合功能函數
    def engineering_mode_init(self):
        """工程模式初始化 - 進入配置模式並開啟工程模式"""
        if not self.is_connected:
            messagebox.showwarning("警告", "請先連接串列埠")
            return
        
        self.log("🔧 開始工程模式初始化...")
        # 進入配置模式
        self.send_command("FD FC FB FA 04 00 FF 00 01 00 04 03 02 01")
        # 等待一下再開啟工程模式
        self.root.after(500, lambda: self.send_command("FD FC FB FA 02 00 62 00 04 03 02 01"))
        # 退出配置模式
        self.root.after(1000, lambda: self.send_command("FD FC FB FA 02 00 FE 00 04 03 02 01"))
        # 查詢參數以確認設定
        self.root.after(1500, lambda: self.send_command("FD FC FB FA 02 00 12 00 04 03 02 01"))
    
    def query_all_settings(self):
        """查詢所有設定 - 一次性查詢所有設備參數（根據協議文檔更新）"""
        if not self.is_connected:
            messagebox.showwarning("警告", "請先連接串列埠")
            return
        
        self.log("📏 開始查詢所有設定...")
        commands = [
            ("FD FC FB FA 04 00 FF 00 01 00 04 03 02 01", "進入配置模式"),
            ("FD FC FB FA 02 00 A0 00 04 03 02 01", "查詢版本"),
            ("FD FC FB FA 04 00 A5 00 01 00 04 03 02 01", "查詢MAC地址"),
            ("FD FC FB FA 02 00 11 00 04 03 02 01", "查詢距離分辨率"),
            ("FD FC FB FA 02 00 12 00 04 03 02 01", "查詢基礎參數"),
            ("FD FC FB FA 02 00 1B 00 04 03 02 01", "查詢背景校正狀態"),
            ("FD FC FB FA 02 00 1C 00 04 03 02 01", "查詢光感輔助控制配置"),  # 新增
            ("FD FC FB FA 02 00 13 00 04 03 02 01", "查詢移動門敏感度"),
            ("FD FC FB FA 02 00 14 00 04 03 02 01", "查詢靜止門敏感度"),
            ("FD FC FB FA 02 00 FE 00 04 03 02 01", "退出配置模式")
        ]
        
        for i, (cmd, desc) in enumerate(commands):
            delay = i * 800  # 每個命令間隔800ms
            self.root.after(delay, lambda c=cmd, d=desc: (
                self.log(f"📊 {d}..."),
                self.send_command(c)
            ))
    
    def standard_config(self):
        """標準配置 - 設定為常用的標準參數"""
        if not self.is_connected:
            messagebox.showwarning("警告", "請先連接串列埠")
            return
        
        self.log("🎯 開始標準配置...")
        commands = [
            ("FD FC FB FA 04 00 FF 00 01 00 04 03 02 01", "進入配置模式"),
            ("FD FC FB FA 08 00 01 00 00 00 00 00 00 00 04 03 02 01", "設定距離分辨率0.75m"),
            ("FD FC FB FA 02 00 63 00 04 03 02 01", "關閉工程模式"),
            ("FD FC FB FA 02 00 FE 00 04 03 02 01", "退出配置模式")
        ]
        
        for i, (cmd, desc) in enumerate(commands):
            delay = i * 600
            self.root.after(delay, lambda c=cmd, d=desc: (
                self.log(f"🎯 {d}..."),
                self.send_command(c)
            ))
    
    def detailed_diagnostics(self):
        """詳細診斷 - 執行完整的設備診斷（根據協議文檔更新）"""
        if not self.is_connected:
            messagebox.showwarning("警告", "請先連接串列埠")
            return
        
        self.log("📊 開始詳細診斷...")
        # 先查詢所有設定
        self.query_all_settings()
        
        # 然後測試工程模式和光感功能
        self.root.after(9000, lambda: (
            self.log("📊 測試工程模式功能..."),
            self.send_command("FD FC FB FA 04 00 FF 00 01 00 04 03 02 01")
        ))
        self.root.after(9500, lambda: self.send_command("FD FC FB FA 02 00 62 00 04 03 02 01"))
        self.root.after(10000, lambda: self.send_command("FD FC FB FA 02 00 12 00 04 03 02 01"))
        self.root.after(10500, lambda: (
            self.log("📊 測試光感輔助控制功能..."),
            self.send_command("FD FC FB FA 02 00 1C 00 04 03 02 01")
        ))
        self.root.after(11000, lambda: self.send_command("FD FC FB FA 02 00 FE 00 04 03 02 01"))
        
        self.log("📊 診斷完成後將在工程模式下輸出數據")
    
    def full_restart(self):
        """完整重啟 - 重啟模組並重新初始化"""
        if not self.is_connected:
            messagebox.showwarning("警告", "請先連接串列埠")
            return
        
        self.log("🔄 開始完整重啟...")
        # 進入配置模式並重啟
        self.send_command("FD FC FB FA 04 00 FF 00 01 00 04 03 02 01")
        self.root.after(500, lambda: self.send_command("FD FC FB FA 02 00 A3 00 04 03 02 01"))
        
        # 重啟後等待3秒再查詢參數
        self.root.after(3000, lambda: (
            self.log("🔄 重啟完成，查詢設備狀態..."),
            self.send_command("FD FC FB FA 02 00 12 00 04 03 02 01")
        ))
    
    def light_control_setup(self):
        """光感輔助控制設定 - 新增功能"""
        if not self.is_connected:
            messagebox.showwarning("警告", "請先連接串列埠")
            return
        
        # 創建光感設定對話框
        dialog = tk.Toplevel(self.root)
        dialog.title("光感輔助控制設定")
        dialog.geometry("400x300")
        dialog.configure(bg=self.colors['bg_dark'])
        
        # 設定深色主題
        dialog.configure(bg=self.colors['bg_dark'])
        
        # 控制模式選擇
        mode_frame = ttk.LabelFrame(dialog, text="控制模式", padding="10")
        mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
        mode_var = tk.StringVar(value="0")
        modes = [
            ("0", "關閉光感輔助控制功能"),
            ("1", "光感值小於閾值時觸發"),
            ("2", "光感值大於閾值時觸發")
        ]
        
        for value, text in modes:
            ttk.Radiobutton(mode_frame, text=text, variable=mode_var, value=value).pack(anchor=tk.W, pady=2)
        
        # 閾值設定
        threshold_frame = ttk.LabelFrame(dialog, text="光感閾值 (0-255)", padding="10")
        threshold_frame.pack(fill=tk.X, padx=10, pady=10)
        
        threshold_var = tk.StringVar(value="80")
        threshold_scale = tk.Scale(threshold_frame, from_=0, to=255, orient=tk.HORIZONTAL, 
                                 variable=threshold_var, length=300,
                                 bg=self.colors['bg_medium'], fg=self.colors['fg_primary'],
                                 highlightbackground=self.colors['bg_dark'])
        threshold_scale.pack(fill=tk.X, pady=5)
        
        threshold_entry = ttk.Entry(threshold_frame, textvariable=threshold_var, width=10)
        threshold_entry.pack(pady=5)
        
        # 常用預設值
        preset_frame = ttk.LabelFrame(dialog, text="常用預設值", padding="10")
        preset_frame.pack(fill=tk.X, padx=10, pady=10)
        
        presets = [
            ("智能照明 (模式1, 閾值50)", "1", "50"),
            ("白天模式 (模式2, 閾值100)", "2", "100"),
            ("夜間模式 (模式1, 閾值80)", "1", "80"),
            ("關閉功能 (模式0)", "0", "0")
        ]
        
        for text, mode, threshold in presets:
            btn = ttk.Button(preset_frame, text=text,
                           command=lambda m=mode, t=threshold: (
                               mode_var.set(m),
                               threshold_var.set(t)
                           ))
            btn.pack(fill=tk.X, pady=2)
        
        # 按鈕區域
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def apply_settings():
            mode = int(mode_var.get())
            threshold = int(threshold_var.get())
            
            # 生成命令
            cmd = f"FD FC FB FA 04 00 0C 00 {mode:02X} {threshold:02X} 04 03 02 01"
            
            self.log(f"💡 設定光感輔助控制: 模式={mode}, 閾值={threshold}")
            
            # 進入配置模式並設定
            self.send_command("FD FC FB FA 04 00 FF 00 01 00 04 03 02 01")
            self.root.after(500, lambda: self.send_command(cmd))
            self.root.after(1000, lambda: self.send_command("FD FC FB FA 02 00 FE 00 04 03 02 01"))
            self.root.after(1500, lambda: self.send_command("FD FC FB FA 02 00 1C 00 04 03 02 01"))
            
            dialog.destroy()
        
        def query_current():
            self.log("💡 查詢當前光感輔助控制設定...")
            self.send_command("FD FC FB FA 04 00 FF 00 01 00 04 03 02 01")
            self.root.after(500, lambda: self.send_command("FD FC FB FA 02 00 1C 00 04 03 02 01"))
            self.root.after(1000, lambda: self.send_command("FD FC FB FA 02 00 FE 00 04 03 02 01"))
        
        ttk.Button(button_frame, text="💡 查詢當前設定", command=query_current).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="✅ 應用設定", command=apply_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="❌ 取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # 居中顯示對話框
        dialog.transient(self.root)
        dialog.grab_set()
        
    def advanced_config_setup(self):
        """進階配置設定 - 新增功能"""
        if not self.is_connected:
            messagebox.showwarning("警告", "請先連接串列埠")
            return
        
        self.log("🎯 開始進階配置...")
        commands = [
            ("FD FC FB FA 04 00 FF 00 01 00 04 03 02 01", "進入配置模式"),
            ("FD FC FB FA 08 00 01 00 00 00 00 00 00 00 04 03 02 01", "設定距離分辨率0.75m"),
            ("FD FC FB FA 07 00 02 00 01 0C 0A 00 00 04 03 02 01", "基礎參數配置(最小門1,最大門12,超時10s)"),
            ("FD FC FB FA 04 00 0C 00 00 00 04 03 02 01", "關閉光感輔助控制"),
            ("FD FC FB FA 02 00 63 00 04 03 02 01", "關閉工程模式"),
            ("FD FC FB FA 02 00 FE 00 04 03 02 01", "退出配置模式"),
            ("FD FC FB FA 02 00 12 00 04 03 02 01", "查詢參數確認")
        ]
        
        for i, (cmd, desc) in enumerate(commands):
            delay = i * 600
            self.root.after(delay, lambda c=cmd, d=desc: (
                self.log(f"🎯 {d}..."),
                self.send_command(c)
            ))
    
    def test_state_parsing(self):
        """測試狀態位解析功能 - 新增調試功能"""
        # 創建狀態測試對話框
        dialog = tk.Toplevel(self.root)
        dialog.title("狀態位解析測試")
        dialog.geometry("500x400")
        dialog.configure(bg=self.colors['bg_dark'])
        
        # 狀態測試區域
        test_frame = ttk.LabelFrame(dialog, text="狀態位解析測試", padding="10")
        test_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 測試結果顯示
        result_text = scrolledtext.ScrolledText(test_frame, height=15, font=("Courier", 11),
                                              bg=self.colors['bg_medium'], 
                                              fg=self.colors['fg_primary'],
                                              insertbackground=self.colors['fg_primary'])
        result_text.pack(fill=tk.BOTH, expand=True)
        
        # 執行狀態測試
        test_results = """🔍 LD2412 狀態位解析測試報告
根據協議文檔進行狀態解析驗證：

📋 協議規範對照表：
┌────────┬──────────┬────────────────────┐
│ 狀態值 │ 二進制   │ 說明               │
├────────┼──────────┼────────────────────┤
│ 0x00   │ 00000000 │ 無目標             │
│ 0x01   │ 00000001 │ 運動目標           │
│ 0x02   │ 00000010 │ 靜止目標           │
│ 0x03   │ 00000011 │ 運動&靜止目標      │
│ 0x04   │ 00000100 │ 正在底噪檢測中     │
│ 0x05   │ 00000101 │ 底噪檢測成功       │
│ 0x06   │ 00000110 │ 底噪檢測失敗       │
└────────┴──────────┴────────────────────┘

🧪 解析測試結果：
"""
        
        result_text.insert(tk.END, test_results)
        
        # 測試所有已知狀態值
        test_states = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0xFF]
        for state in test_states:
            parsed_text = self.get_state_text(state)
            result_text.insert(tk.END, f"狀態 0x{state:02X}: {parsed_text}\n")
        
        result_text.insert(tk.END, f"\n✅ 解析函數已根據協議文檔修正\n")
        result_text.insert(tk.END, f"✅ 統計函數已根據協議文檔修正\n")
        result_text.insert(tk.END, f"\n⚠️  注意：其他GUI文件可能仍使用舊的位掩碼邏輯\n")
        result_text.insert(tk.END, f"建議檢查以下文件：\n")
        result_text.insert(tk.END, f"- ld2412_gui.py\n")
        result_text.insert(tk.END, f"- ld2412_simple_gui.py\n") 
        result_text.insert(tk.END, f"- ld2412_analyzer.py\n")
        result_text.insert(tk.END, f"- ld2412_cli.py\n")
        
        # 關閉按鈕
        ttk.Button(dialog, text="關閉", command=dialog.destroy).pack(pady=10)
        
        # 居中顯示對話框
        dialog.transient(self.root)
        dialog.grab_set()
        
        self.log("🧪 已執行狀態位解析測試")
    
    def test_sensitivity_update(self):
        """測試敏感度更新功能"""
        self.log("🔍 開始測試敏感度更新功能...")
        
        # 顯示當前敏感度狀態
        self.log(f"📊 當前移動門敏感度數量: {len(self.moving_gate_sensitivities)}")
        self.log(f"📊 當前靜止門敏感度數量: {len(self.still_gate_sensitivities)}")
        
        if len(self.moving_gate_sensitivities) >= 14:
            moving_sens = ','.join([str(s) for s in self.moving_gate_sensitivities[:14]])
            self.log(f"   移動門: {moving_sens}")
        
        if len(self.still_gate_sensitivities) >= 14:
            still_sens = ','.join([str(s) for s in self.still_gate_sensitivities[:14]])
            self.log(f"   靜止門: {still_sens}")
        
        # 模擬測試數據（如果沒有實際數據）
        if len(self.moving_gate_sensitivities) < 14:
            self.log("⚠️  尚未查詢到實際敏感度數據，使用測試數據...")
            # 創建測試敏感度數據
            test_moving = [30, 35, 25, 40, 45, 30, 35, 25, 30, 35, 40, 30, 25, 35]
            test_still = [20, 25, 15, 30, 35, 20, 25, 15, 20, 25, 30, 20, 15, 25]
            
            self.moving_gate_sensitivities = test_moving
            self.still_gate_sensitivities = test_still
            
            self.log(f"📊 已設定測試敏感度數據")
            self.log(f"   移動門敏感度: {','.join([str(s) for s in test_moving[:7]])}...")
            self.log(f"   靜止門敏感度: {','.join([str(s) for s in test_still[:7]])}...")
        
        # 強制更新圖表 - 只更新個別門標記
        if MATPLOTLIB_AVAILABLE and hasattr(self, 'ax1') and hasattr(self, 'ax2'):
            self.log("🔄 正在更新個別門敏感度標記...")
            self.update_sensitivity_reference_lines()  # 清除平均參考線
            self.draw_individual_sensitivity_markers()  # 繪製個別門標記
            if hasattr(self, 'canvas'):
                self.canvas.draw()
            self.log("✅ 個別門敏感度標記更新完成")
        else:
            self.log("⚠️  matplotlib不可用或圖表未初始化")
        
        self.log("🔍 敏感度測試完成！請檢查門能量圖分頁中每個門的紅色敏感度標記線和數值標籤")
    
    def force_refresh_charts(self):
        """強制刷新圖表 - 測試用"""
        try:
            if not MATPLOTLIB_AVAILABLE:
                self.log("⚠️ matplotlib 不可用，無法刷新圖表")
                return
                
            self.log("🔄 強制刷新圖表...")
            
            # 顯示當前個別門敏感度數據
            if len(self.moving_gate_sensitivities) >= 14:
                moving_sens = ','.join([str(s) for s in self.moving_gate_sensitivities[:7]])
                self.log(f"🎯 當前移動門敏感度(0-6): {moving_sens}...")
            else:
                self.log(f"🎯 當前移動門敏感度: 尚未設定")
                
            if len(self.still_gate_sensitivities) >= 14:
                still_sens = ','.join([str(s) for s in self.still_gate_sensitivities[:7]])
                self.log(f"🎯 當前靜止門敏感度(0-6): {still_sens}...")
            else:
                self.log(f"🎯 當前靜止門敏感度: 尚未設定")
            
            # 檢查圖表是否存在
            if hasattr(self, 'ax1') and hasattr(self, 'ax2'):
                # 清除平均敏感度參考線
                self.update_sensitivity_reference_lines()
                
                # 強制繪製個別門敏感度標記
                self.draw_individual_sensitivity_markers()
                
                # 強制重繪圖表
                if hasattr(self, 'canvas'):
                    self.canvas.draw()
                    self.log("✅ 個別門敏感度標記已強制刷新")
                else:
                    self.log("⚠️ 無法找到canvas物件")
            else:
                self.log("⚠️ 圖表軸線不存在，請先開啟工程模式獲取數據")
                
        except Exception as e:
            self.log(f"❌ 強制刷新圖表失敗: {e}")
            print(f"強制刷新錯誤: {e}")
    
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
    print("啟動LD2412深色主題GUI控制系統...")
    app = DarkLD2412GUI()
    app.run()

if __name__ == "__main__":
    main() 