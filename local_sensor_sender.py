import serial
import time
import requests

PORT = '/dev/ttyACM0' 
BAUDRATE = 115200

# ⚠️ Render 서버 배포 후 생성된 본인의 웹 서비스 도메인 주소로 변경하세요.
RENDER_SERVER_URL = "https://your-app-name.onrender.com/api/sensor"

def main():
    try:
        py_serial = serial.Serial(port=PORT, baudrate=BAUDRATE, timeout=1)
        time.sleep(2)
        print("센서 데이터 수집 및 클라우드 전송 시작...")
        
        while True:
            if py_serial.in_waiting > 0:
                line = py_serial.readline().decode('utf-8').strip()
                if "Weight:" in line and "Temp:" in line:
                    parts = line.split('|')
                    weight = float(parts[0].replace("Weight:", "").replace("kg", "").strip())
                    temp = float(parts[1].replace("Temp:", "").replace("C", "").strip())
                    humid = float(parts[2].replace("Humid:", "").replace("%", "").strip())

                    payload = {
                        "weight": weight,
                        "temp": temp,
                        "humid": humid
                    }

                    try:
                        res = requests.post(RENDER_SERVER_URL, json=payload, timeout=5)
                        print(f"[전송 성공] {payload} | Status: {res.status_code}")
                    except requests.exceptions.RequestException as e:
                        print(f"[전송 실패] 서버 연결 오류: {e}")
            time.sleep(0.1)
    except Exception as e:
        print(f"Serial Error: {e}")

if __name__ == '__main__':
    main()