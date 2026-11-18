from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

app = Flask(__name__)

# Gemini connection
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Dashboard
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# Chatbot page
@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")


# Construction cost prediction
@app.route("/predict", methods=["POST"])
def predict():

    data = request.get_json()

    area = float(data.get("area", 0))
    floors = int(data.get("floors", 1))
    quality = data.get("quality", "Standard")

    if area <= 0 or floors <= 0:
        return jsonify({"error": "Enter valid area and floors"}), 400

    # Approximate rates per square foot in INR
    rates = {
        "Basic": 1600,
        "Standard": 1900,
        "Premium": 2400
    }

    rate = rates.get(quality, 1900)

    total_area = area * floors
    total_cost = total_area * rate

    materials = {
        "Cement": total_cost * 0.16,
        "Steel": total_cost * 0.25,
        "Bricks": total_cost * 0.10,
        "Labour": total_cost * 0.20,
        "Flooring": total_cost * 0.09,
        "Painting": total_cost * 0.05,
        "Electrical": total_cost * 0.08,
        "Other": total_cost * 0.07
    }

    return jsonify({
        "area": total_area,
        "rate": rate,
        "total_cost": round(total_cost, 2),
        "materials": materials
    })


# Gemini AI chatbot
@app.route("/chat", methods=["POST"])
def chat():

    if client is None:
        return jsonify({"error": "Gemini API key not found"}), 500

    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Please enter a question"}), 400

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=(
                "You are BuildNest AI, a helpful house construction "
                "assistant. Answer questions about construction, "
                "materials, budgeting and cost saving in simple English.\n\n"
                + message
            )
        )

        return jsonify({"reply": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)

