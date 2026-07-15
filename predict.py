from ultralytics import YOLO
import cv2
import requests

model = YOLO("yolov11_custom.pt")

FLASK_URL = "http://127.0.0.1:5000/alert"


# ---------------- 1. MOBILE GPS (highest accuracy) ----------------
def get_mobile_location():
    try:
        r = requests.get("http://127.0.0.1:5000/mobile_location", timeout=5)
        data = r.json()
        if data.get("lat") and data.get("lon"):
            return data["lat"], data["lon"]
    except:
        pass
    return None, None


# ---------------- 2. GOOGLE IP LOCATION ----------------
def get_google_location():
    try:
        r = requests.get("http://127.0.0.1:5000/get_google_location", timeout=5)
        data = r.json()
        if data.get("lat") and data.get("lon"):
            return data["lat"], data["lon"]
    except:
        pass
    return None, None


# ---------------- SELECT BEST ----------------
def get_best_location():
    lat, lon = get_mobile_location()
    if lat:
        print("📍 Using Mobile GPS")
        return lat, lon

    lat, lon = get_google_location()
    if lat:
        print("🌍 Using Google IP Location")
        return lat, lon

    print("❗ Using fallback location")
    return 12.9141, 74.8560


# ---------------- YOLO DETECTION ----------------
source = "a.jpg"
results = model.predict(source=source, stream=True, show=True,conf=0.7 )

alert_sent = False

for r in results:
    detected = False

    for box in r.boxes:
        label = model.names[int(box.cls)]
        if label.lower() == "short-circuit":
            detected = True
            break

    if detected and not alert_sent:
        print("⚡ Alert: Short-circuit detected!")

        frame_path = "detected_frame.jpg"
        cv2.imwrite(frame_path, r.plot())

        lat, lon = get_best_location()
        location_url = f"https://maps.google.com/?q={lat},{lon}"

        data = {
            "pole_id": "Pole 2",
            "location": location_url,
            "message": "⚠️ Short Circuit Detected!"
        }

        with open(frame_path, "rb") as f:
            requests.post(FLASK_URL, data=data, files={"image": f})

        print("✅ Alert sent!")
        alert_sent = True
        break

cv2.destroyAllWindows()
