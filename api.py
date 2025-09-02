# api.py
from flask import Flask, request, jsonify
from detector_v2 import analyze_text
import db_utils

app = Flask(__name__)

# Initialize DB
db_utils.init_db()

@app.route("/")
def home():
    return jsonify({"message": "AI vs Human Content Detector API is running 🚀"})

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' field"}), 400

    text = data["text"]
    result = analyze_text(text)

    # Log to DB
    db_utils.log_result(
        text,
        result["prediction"],
        result["confidence"],
        result["features"].get("n_words", 0)
    )

    return jsonify(result)

@app.route("/history", methods=["GET"])
def history():
    rows = db_utils.fetch_all()
    history = [
        {
            "id": r[0],
            "timestamp": r[1],
            "text_hash": r[2],
            "prediction": r[3],
            "confidence": r[4],
            "n_words": r[5]
        }
        for r in rows
    ]
    return jsonify(history)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
