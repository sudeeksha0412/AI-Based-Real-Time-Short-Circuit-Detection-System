from flask import Flask, request, jsonify, render_template, send_from_directory, url_for
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from pytz import timezone
import requests

app = Flask(__name__)

# Folder to store images
ALERT_DIR = os.path.join(app.root_path, "received_alerts")
os.makedirs(ALERT_DIR, exist_ok=True)

# Alerts (reset on restart)
alerts = []

# Mobile exact GPS
mobile_location = {"lat": None, "lon": None}


# ---------------- DASHBOARD ----------------
@app.route("/")
def dashboard():
    return render_template("index.html", alerts=list(reversed(alerts)))


# ---------------- ALERT FROM YOLO ----------------
@app.route("/alert", methods=["POST"])
def receive_alert():
    data = request.form
    image = request.files.get("image")

    pole = data.get("pole_id", "Unknown")
    location = data.get("location", "N/A")
    message = data.get("message", "")

    # India Time
    india_time = datetime.now(timezone("Asia/Kolkata"))
    timestamp = india_time.strftime("%d %b %Y, %I:%M %p")

    # Save Image
    image_url = None
    if image:
        safe_name = secure_filename(image.filename)
        image_filename = f"{timestamp.replace(':','-')}_{safe_name}"
        save_path = os.path.join(ALERT_DIR, image_filename)
        image.save(save_path)
        image_url = url_for("get_alert_image", filename=image_filename)

    # Add Alert
    alert = {
        "time": timestamp,
        "pole": pole,
        "location": location,
        "message": message,
        "image": image_url,
        "status": "pending"
    }

    alerts.append(alert)
    print("📩 New Alert Received")

    return jsonify({"status": "success"})


# ---------------- UPDATE STATUS ----------------
@app.route("/update_status", methods=["POST"])
def update_status():
    data = request.get_json()
    idx = data.get("index")
    status = data.get("status")

    if idx is not None and 0 <= idx < len(alerts):
        alerts[len(alerts) - 1 - idx]["status"] = status
        return jsonify({"ok": True})

    return jsonify({"ok": False}), 400


# ---------------- IMAGE SERVE ----------------
@app.route("/received_alerts/<path:filename>")
def get_alert_image(filename):
    return send_from_directory(ALERT_DIR, filename)


# ---------------- MOBILE GPS PAGE ----------------
@app.route("/location")
def location_page():
    return render_template("location.html")


@app.route("/mobile_location", methods=["POST"])
def receive_mobile_location():
    data = request.get_json()
    mobile_location["lat"] = data.get("lat")
    mobile_location["lon"] = data.get("lon")

    print("📍 Mobile GPS Updated:", mobile_location)
    return jsonify({"ok": True})


@app.route("/mobile_location", methods=["GET"])
def send_mobile_location():
    return jsonify(mobile_location)


# ---------------- GOOGLE IP LOCATION ----------------
@app.route("/google_location")
def google_location_page():
    return render_template("google_location.html")


@app.route("/get_google_location")
def get_google_location():
    try:
        resp = requests.get("https://ipinfo.io/json", timeout=5)
        data = resp.json()
        loc = data.get("loc")

        if loc:
            lat, lon = map(float, loc.split(","))
            return jsonify({
                "lat": lat,
                "lon": lon,
                "accuracy": 15000
            })
    except:
        pass

    return jsonify({"lat": None, "lon": None, "accuracy": None})


# ---------------- RUN ----------------
if __name__ == "__main__":
    print("🚀 Server fresh started. All old alerts cleared.")
    app.run(host="0.0.0.0", port=5000)
