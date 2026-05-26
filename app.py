from flask import Flask, render_template, jsonify, request
import threading
import time
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# 💡 오늘 기준 최근 7일 날짜(MM/DD) 자동 생성 함수
def get_last_7_days():
    today = datetime.now()
    # 6일 전부터 오늘까지 배열 생성
    return [(today - timedelta(days=i)).strftime("%m/%d") for i in range(6, -1, -1)]

# 전역 데이터 저장소
data_store = {
    "temp": 0.0,
    "humid": 0.0,
    "co2": None,
    "o2": None,
    "fsm_state": None,
    "current_weight": 0.0,
    "today_harvest": 0.0,
    "temp_history": [], 
    "humid_history": [],
    "daily_harvest_labels": get_last_7_days(),
    # 💡 과거 데이터는 없으므로 모두 0으로 초기화 (배열의 맨 마지막 요소가 '오늘'입니다)
    "daily_harvest_data": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] 
}

last_weight = 0.0
current_date = datetime.now().strftime("%Y-%m-%d") # 날짜 변경 감지용 변수

def check_date_change():
    """자정이 지나면 그래프 날짜 라벨과 데이터를 하루씩 미루는 함수"""
    global current_date
    now_date = datetime.now().strftime("%Y-%m-%d")
    
    if now_date != current_date:
        current_date = now_date
        # 날짜 라벨 갱신 (내일이 되면 내일 날짜가 맨 끝으로 옴)
        data_store["daily_harvest_labels"] = get_last_7_days()
        
        # 데이터는 과거로 한 칸씩 밀고(가장 오래된 앞의 데이터 삭제), 오늘 수확량은 0으로 초기화
        data_store["daily_harvest_data"].pop(0)
        data_store["daily_harvest_data"].append(0.0)   
        data_store["today_harvest"] = 0.0

def history_scheduler():
    while True:
        now = datetime.now().strftime("%H:%M")
        data_store["temp_history"].append({"x": now, "y": data_store["temp"]})
        data_store["humid_history"].append({"x": now, "y": data_store["humid"]})
        
        # 1분마다 측정하며, 최대 최근 20개의 데이터만 화면에 유지
        if len(data_store["temp_history"]) > 20:
            data_store["temp_history"].pop(0)
            data_store["humid_history"].pop(0)
        
        time.sleep(60)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    return jsonify(data_store)

@app.route('/api/sensor', methods=['POST'])
def receive_sensor_data():
    global last_weight
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
        
    weight = data.get("weight", 0.0)
    
    data_store["temp"] = data.get("temp", 0.0)
    data_store["humid"] = data.get("humid", 0.0)
    data_store["current_weight"] = weight

    check_date_change() 

    if weight >= 1.0 and weight != last_weight:
        added_weight = weight - last_weight if weight > last_weight else 0
        data_store["today_harvest"] = round(data_store["today_harvest"] + added_weight, 2)
        last_weight = weight
        data_store["daily_harvest_data"][-1] = data_store["today_harvest"]

    return jsonify({"status": "success", "today_harvest": data_store["today_harvest"]}), 200

if __name__ == '__main__':
    threading.Thread(target=history_scheduler, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)