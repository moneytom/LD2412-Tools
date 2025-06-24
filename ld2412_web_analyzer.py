#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, jsonify, request
import serial
import threading
import time
import json
from datetime import datetime
from collections import deque
import os

app = Flask(__name__)

# 全局變數
serial_port = None
is_connected = False
is_monitoring = False
port_name = "/dev/cu.usbserial-0001"
baud_rate = 115200

# 數據存儲
data_history = {
    'time': deque(maxlen=100),
    'moving_distance': deque(maxlen=100),
    'moving_energy': deque(maxlen=100),
    'still_distance': deque(maxlen=100),
    'still_energy': deque(maxlen=100),
    'detection_distance': deque(maxlen=100),
    'target_state': deque(maxlen=100)
}

# 統計數據
stats = {
    'total_frames': 0,
    'moving_detections': 0,
    'still_detections': 0,
    'no_target': 0,
    'max_distance': 0,
    'min_distance': 9999,
    'avg_moving_distance': 0,
    'avg_still_distance': 0
}

# 行為模式
patterns = {
    'approach': 0,
    'leave': 0,
    'stable': 0,
    'noise': 0
}

# 原始數據緩衝區
raw_buffer = bytearray()

# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>LD2412 雷達數據分析系統</title>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .control-panel {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .control-panel button {
            padding: 10px 20px;
            margin: 5px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .btn-connect { background-color: #3498db; color: white; }
        .btn-monitor { background-color: #2ecc71; color: white; }
        .btn-start { background-color: #e74c3c; color: white; }
        .btn-clear { background-color: #95a5a6; color: white; }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 20px;
        }
        .data-panel {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .chart-container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .realtime-data {
            margin-bottom: 20px;
        }
        .realtime-data h3 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .data-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #ecf0f1;
        }
        .data-value {
            font-weight: bold;
            color: #3498db;
        }
        .stats-panel {
            margin-top: 20px;
        }
        .pattern-panel {
            margin-top: 20px;
        }
        .log-panel {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-top: 20px;
            height: 200px;
            overflow-y: auto;
        }
        .log-entry {
            padding: 4px 0;
            font-size: 12px;
            color: #7f8c8d;
        }
        #status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
        }
        .status-connected { background-color: #2ecc71; color: white; }
        .status-disconnected { background-color: #e74c3c; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>LD2412 雷達數據分析系統</h1>
            <p>即時數據視覺化與行為模式分析</p>
        </div>
        
        <div class="control-panel">
            <button class="btn-connect" onclick="toggleConnection()">連接設備</button>
            <button class="btn-monitor" onclick="toggleMonitoring()">開始監控</button>
            <button class="btn-start" onclick="sendStartCommand()">發送啟動命令</button>
            <button class="btn-clear" onclick="clearData()">清除數據</button>
            <span id="status" class="status-disconnected">未連接</span>
        </div>
        
        <div class="main-content">
            <div class="left-panel">
                <div class="data-panel realtime-data">
                    <h3>📊 即時數據</h3>
                    <div class="data-item">
                        <span>目標狀態:</span>
                        <span class="data-value" id="target_state">--</span>
                    </div>
                    <div class="data-item">
                        <span>移動距離:</span>
                        <span class="data-value" id="moving_distance">--</span>
                    </div>
                    <div class="data-item">
                        <span>移動能量:</span>
                        <span class="data-value" id="moving_energy">--</span>
                    </div>
                    <div class="data-item">
                        <span>靜止距離:</span>
                        <span class="data-value" id="still_distance">--</span>
                    </div>
                    <div class="data-item">
                        <span>靜止能量:</span>
                        <span class="data-value" id="still_energy">--</span>
                    </div>
                    <div class="data-item">
                        <span>檢測距離:</span>
                        <span class="data-value" id="detection_distance">--</span>
                    </div>
                </div>
                
                <div class="data-panel stats-panel">
                    <h3>📈 統計分析</h3>
                    <div id="stats_content">等待數據...</div>
                </div>
                
                <div class="data-panel pattern-panel">
                    <h3>🎯 行為模式</h3>
                    <div id="pattern_content">等待數據...</div>
                </div>
            </div>
            
            <div class="right-panel">
                <div class="chart-container">
                    <h3>距離趨勢分析</h3>
                    <canvas id="distanceChart"></canvas>
                </div>
                
                <div class="chart-container">
                    <h3>能量分布分析</h3>
                    <canvas id="energyChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="log-panel">
            <h3>📝 分析日誌</h3>
            <div id="log_content"></div>
        </div>
    </div>
    
    <script>
        // 圖表初始化
        const distanceCtx = document.getElementById('distanceChart').getContext('2d');
        const energyCtx = document.getElementById('energyChart').getContext('2d');
        
        const distanceChart = new Chart(distanceCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '移動距離',
                    data: [],
                    borderColor: 'rgb(52, 152, 219)',
                    tension: 0.1
                }, {
                    label: '靜止距離',
                    data: [],
                    borderColor: 'rgb(231, 76, 60)',
                    tension: 0.1
                }, {
                    label: '檢測距離',
                    data: [],
                    borderColor: 'rgb(46, 204, 113)',
                    borderDash: [5, 5],
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '距離 (cm)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: '時間 (秒)'
                        }
                    }
                }
            }
        });
        
        const energyChart = new Chart(energyCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '移動能量',
                    data: [],
                    borderColor: 'rgb(52, 152, 219)',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.1
                }, {
                    label: '靜止能量',
                    data: [],
                    borderColor: 'rgb(231, 76, 60)',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '能量值'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: '時間 (秒)'
                        }
                    }
                }
            }
        });
        
        // API調用函數
        function toggleConnection() {
            fetch('/api/toggle_connection', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    updateStatus(data.connected);
                    addLog(data.message);
                });
        }
        
        function toggleMonitoring() {
            fetch('/api/toggle_monitoring', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    addLog(data.message);
                });
        }
        
        function sendStartCommand() {
            fetch('/api/send_start_command', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    addLog(data.message);
                });
        }
        
        function clearData() {
            fetch('/api/clear_data', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    addLog(data.message);
                    // 清除圖表
                    distanceChart.data.labels = [];
                    distanceChart.data.datasets.forEach(dataset => dataset.data = []);
                    distanceChart.update();
                    
                    energyChart.data.labels = [];
                    energyChart.data.datasets.forEach(dataset => dataset.data = []);
                    energyChart.update();
                });
        }
        
        function updateStatus(connected) {
            const statusEl = document.getElementById('status');
            if (connected) {
                statusEl.textContent = '已連接';
                statusEl.className = 'status-connected';
            } else {
                statusEl.textContent = '未連接';
                statusEl.className = 'status-disconnected';
            }
        }
        
        function addLog(message) {
            const logContent = document.getElementById('log_content');
            const timestamp = new Date().toLocaleTimeString();
            logContent.innerHTML += `<div class="log-entry">[${timestamp}] ${message}</div>`;
            logContent.scrollTop = logContent.scrollHeight;
        }
        
        // 定期更新數據
        function updateData() {
            fetch('/api/get_data')
                .then(response => response.json())
                .then(data => {
                    // 更新即時數據
                    document.getElementById('target_state').textContent = data.realtime.target_state;
                    document.getElementById('moving_distance').textContent = data.realtime.moving_distance + ' cm';
                    document.getElementById('moving_energy').textContent = data.realtime.moving_energy;
                    document.getElementById('still_distance').textContent = data.realtime.still_distance + ' cm';
                    document.getElementById('still_energy').textContent = data.realtime.still_energy;
                    document.getElementById('detection_distance').textContent = data.realtime.detection_distance + ' cm';
                    
                    // 更新統計
                    document.getElementById('stats_content').innerHTML = data.stats_html;
                    
                    // 更新模式
                    document.getElementById('pattern_content').innerHTML = data.pattern_html;
                    
                    // 更新圖表
                    if (data.history.time.length > 0) {
                        distanceChart.data.labels = data.history.time;
                        distanceChart.data.datasets[0].data = data.history.moving_distance;
                        distanceChart.data.datasets[1].data = data.history.still_distance;
                        distanceChart.data.datasets[2].data = data.history.detection_distance;
                        distanceChart.update();
                        
                        energyChart.data.labels = data.history.time;
                        energyChart.data.datasets[0].data = data.history.moving_energy;
                        energyChart.data.datasets[1].data = data.history.still_energy;
                        energyChart.update();
                    }
                });
        }
        
        // 每500ms更新一次
        setInterval(updateData, 500);
        
        // 初始化
        addLog('系統啟動，等待連接...');
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/api/toggle_connection', methods=['POST'])
def api_toggle_connection():
    global serial_port, is_connected, is_monitoring
    
    if not is_connected:
        try:
            serial_port = serial.Serial(port_name, baud_rate, timeout=1)
            is_connected = True
            return jsonify({'connected': True, 'message': f'✅ 成功連接到 {port_name}'})
        except Exception as e:
            return jsonify({'connected': False, 'message': f'❌ 連接失敗: {str(e)}'})
    else:
        if serial_port:
            serial_port.close()
        is_connected = False
        is_monitoring = False
        return jsonify({'connected': False, 'message': '已斷開連接'})

@app.route('/api/toggle_monitoring', methods=['POST'])
def api_toggle_monitoring():
    global is_monitoring
    
    if not is_connected:
        return jsonify({'message': '⚠️ 請先連接串列埠'})
    
    is_monitoring = not is_monitoring
    if is_monitoring:
        return jsonify({'message': '🔍 開始監控數據...'})
    else:
        return jsonify({'message': '⏹️ 停止監控'})

@app.route('/api/send_start_command', methods=['POST'])
def api_send_start_command():
    if not is_connected:
        return jsonify({'message': '⚠️ 請先連接串列埠'})
    
    try:
        cmd = bytes.fromhex("FD FC FB FA 02 00 12 00 04 03 02 01")
        serial_port.write(cmd)
        serial_port.flush()
        return jsonify({'message': '📤 已發送啟動命令'})
    except Exception as e:
        return jsonify({'message': f'❌ 發送失敗: {str(e)}'})

@app.route('/api/clear_data', methods=['POST'])
def api_clear_data():
    global stats, patterns
    
    # 清除歷史數據
    for key in data_history:
        data_history[key].clear()
    
    # 重置統計
    stats = {
        'total_frames': 0,
        'moving_detections': 0,
        'still_detections': 0,
        'no_target': 0,
        'max_distance': 0,
        'min_distance': 9999,
        'avg_moving_distance': 0,
        'avg_still_distance': 0
    }
    
    # 重置模式
    for key in patterns:
        patterns[key] = 0
    
    return jsonify({'message': '🗑️ 已清除所有數據'})

@app.route('/api/get_data')
def api_get_data():
    # 準備即時數據
    realtime = {
        'target_state': '--',
        'moving_distance': '--',
        'moving_energy': '--',
        'still_distance': '--',
        'still_energy': '--',
        'detection_distance': '--'
    }
    
    if len(data_history['target_state']) > 0:
        latest_state = data_history['target_state'][-1]
        state_text = "無目標"
        if latest_state & 0x01:
            state_text = ""
            if latest_state & 0x02:
                state_text += "移動 "
            if latest_state & 0x04:
                state_text += "靜止"
        
        realtime['target_state'] = state_text
        realtime['moving_distance'] = data_history['moving_distance'][-1]
        realtime['moving_energy'] = data_history['moving_energy'][-1]
        realtime['still_distance'] = data_history['still_distance'][-1]
        realtime['still_energy'] = data_history['still_energy'][-1]
        realtime['detection_distance'] = data_history['detection_distance'][-1]
    
    # 準備統計HTML
    stats_html = generate_stats_html()
    
    # 準備模式HTML
    pattern_html = generate_pattern_html()
    
    # 準備歷史數據
    history = {
        'time': list(data_history['time']),
        'moving_distance': list(data_history['moving_distance']),
        'moving_energy': list(data_history['moving_energy']),
        'still_distance': list(data_history['still_distance']),
        'still_energy': list(data_history['still_energy']),
        'detection_distance': list(data_history['detection_distance'])
    }
    
    return jsonify({
        'realtime': realtime,
        'stats_html': stats_html,
        'pattern_html': pattern_html,
        'history': history
    })

def generate_stats_html():
    total = stats['total_frames']
    if total == 0:
        return "等待數據..."
    
    moving_rate = (stats['moving_detections'] / total) * 100
    still_rate = (stats['still_detections'] / total) * 100
    no_target_rate = (stats['no_target'] / total) * 100
    
    return f"""
    <div class="data-item">
        <span>總數據幀:</span>
        <span class="data-value">{total}</span>
    </div>
    <div class="data-item">
        <span>移動檢測:</span>
        <span class="data-value">{stats['moving_detections']} ({moving_rate:.1f}%)</span>
    </div>
    <div class="data-item">
        <span>靜止檢測:</span>
        <span class="data-value">{stats['still_detections']} ({still_rate:.1f}%)</span>
    </div>
    <div class="data-item">
        <span>無目標:</span>
        <span class="data-value">{stats['no_target']} ({no_target_rate:.1f}%)</span>
    </div>
    <div class="data-item">
        <span>距離範圍:</span>
        <span class="data-value">{stats['min_distance']} - {stats['max_distance']} cm</span>
    </div>
    """

def generate_pattern_html():
    total_patterns = sum(patterns.values())
    if total_patterns == 0:
        return "等待數據..."
    
    dominant = max(patterns, key=patterns.get) if any(patterns.values()) else None
    patterns_cn = {
        'approach': '接近行為',
        'leave': '離開行為',
        'stable': '穩定存在',
        'noise': '環境干擾'
    }
    
    return f"""
    <div class="data-item">
        <span>接近模式:</span>
        <span class="data-value">{patterns['approach']} 次</span>
    </div>
    <div class="data-item">
        <span>離開模式:</span>
        <span class="data-value">{patterns['leave']} 次</span>
    </div>
    <div class="data-item">
        <span>穩定模式:</span>
        <span class="data-value">{patterns['stable']} 次</span>
    </div>
    <div class="data-item">
        <span>雜訊干擾:</span>
        <span class="data-value">{patterns['noise']} 次</span>
    </div>
    <div class="data-item">
        <span>主要行為:</span>
        <span class="data-value">{patterns_cn.get(dominant, '數據不足')}</span>
    </div>
    """

def data_reader():
    global raw_buffer
    
    while True:
        if is_connected and serial_port and is_monitoring:
            try:
                if serial_port.in_waiting:
                    data = serial_port.read(serial_port.in_waiting)
                    raw_buffer.extend(data)
                    analyze_frames()
            except Exception as e:
                print(f"讀取錯誤: {e}")
        time.sleep(0.01)

def analyze_frames():
    global raw_buffer
    
    buffer = bytes(raw_buffer)
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
                parse_frame(frame)
                i = end_pos
            else:
                i += 1
        else:
            i += 1
    
    # 清理已處理的數據
    if len(raw_buffer) > 1000:
        raw_buffer = raw_buffer[-500:]

def parse_frame(frame):
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
    current_time = len(data_history['time']) * 0.1
    data_history['time'].append(round(current_time, 1))
    data_history['moving_distance'].append(move_dist)
    data_history['moving_energy'].append(move_energy)
    data_history['still_distance'].append(still_dist)
    data_history['still_energy'].append(still_energy)
    data_history['detection_distance'].append(detect_dist)
    data_history['target_state'].append(target_state)
    
    # 更新統計
    stats['total_frames'] += 1
    
    if target_state & 0x01:  # 有目標
        if target_state & 0x02:  # 移動目標
            stats['moving_detections'] += 1
        if target_state & 0x04:  # 靜止目標
            stats['still_detections'] += 1
    else:
        stats['no_target'] += 1
    
    # 更新最大最小距離
    if detect_dist > 0:
        stats['max_distance'] = max(stats['max_distance'], detect_dist)
        stats['min_distance'] = min(stats['min_distance'], detect_dist)
    
    # 分析行為模式
    analyze_patterns()

def analyze_patterns():
    if len(data_history['detection_distance']) < 10:
        return
    
    # 分析最近10個數據點的趨勢
    recent_distances = list(data_history['detection_distance'])[-10:]
    recent_states = list(data_history['target_state'])[-10:]
    
    # 計算距離變化趨勢
    if all(d > 0 for d in recent_distances):
        distance_diff = recent_distances[-1] - recent_distances[0]
        
        if distance_diff < -50:  # 接近超過50cm
            patterns['approach'] += 1
        elif distance_diff > 50:  # 遠離超過50cm
            patterns['leave'] += 1
        else:
            patterns['stable'] += 1
    
    # 檢測雜訊
    state_changes = sum(1 for i in range(1, len(recent_states)) 
                       if recent_states[i] != recent_states[i-1])
    if state_changes > 5:
        patterns['noise'] += 1

if __name__ == '__main__':
    # 啟動數據讀取線程
    data_thread = threading.Thread(target=data_reader, daemon=True)
    data_thread.start()
    
    print("=" * 60)
    print("LD2412 網頁數據分析系統")
    print("=" * 60)
    print("請在瀏覽器中打開: http://localhost:5000")
    print("按 Ctrl+C 退出")
    print("=" * 60)
    
    # 啟動Flask服務器
    app.run(host='0.0.0.0', port=5000, debug=False) 