import os
import time

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai

# =====================================
# 1. INITIAL CONFIGURATION
# =====================================

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

client = None

if API_KEY:
    try:
        client = genai.Client(api_key=API_KEY)
        print("Gemini API connected successfully!", flush=True)
    except Exception as e:
        print("Gemini connection error:", str(e), flush=True)
else:
    print("WARNING: GEMINI_API_KEY not found!", flush=True)


# =====================================
# 2. HOME PAGE
# =====================================

@app.route("/")
def home():
    return render_template("index.html")


# =====================================
# 3. DASHBOARD
# =====================================

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# =====================================
# 4. CHATBOT PAGE
# =====================================

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")


# =====================================
# 5. CONSTRUCTION COST CALCULATOR
# =====================================

@app.route("/predict", methods=["POST"])
def predict():

    try:
        data = request.get_json(silent=True) or {}

        area = float(data.get("area", 0))
        floors = int(data.get("floors", 1))
        quality = str(data.get("quality", "standard")).lower().strip()

        if area <= 0 or floors <= 0 or floors > 10:
            return jsonify({
                "error": "Enter valid area and floors (1-10)."
            }), 400

        rates = {
            "basic": 1500,
            "standard": 2000,
            "premium": 2500
        }

        if quality not in rates:
            return jsonify({
                "error": "Choose Basic, Standard or Premium."
            }), 400

        # Area means total built-up area.
        rate = rates[quality]
        total_cost = area * rate

        percentages = {
            "Cement": 0.16,
            "Steel": 0.25,
            "Sand": 0.08,
            "Bricks / Blocks": 0.15,
            "Aggregate": 0.08,
            "Tiles and Finishing": 0.12,
            "Electrical and Plumbing": 0.09,
            "Paint and Other Materials": 0.07
        }

        materials = {
            name: round(total_cost * percentage, 2)
            for name, percentage in percentages.items()
        }

        return jsonify({
            "area": area,
            "floors": floors,
            "quality": quality.title(),
            "rate_per_sqft": rate,
            "total_cost": round(total_cost, 2),
            "estimated_cost": round(total_cost, 2),
            "materials": materials,
            "message": "Approximate educational estimate only."
        }), 200

    except (ValueError, TypeError):
        return jsonify({
            "error": "Please enter valid numeric values."
        }), 400

    except Exception as e:
        print("Prediction error:", str(e), flush=True)

        return jsonify({
            "error": "Unable to calculate construction cost."
        }), 500


# =====================================
# 6. BUILDNEST AI CHATBOT
# =====================================

@app.route("/chat", methods=["POST"])
def chat():

    print("CHAT ROUTE RECEIVED A REQUEST", flush=True)

    if client is None:
        return jsonify({
            "error": "Gemini API key is missing. Check your .env file."
        }), 500

    try:
        data = request.get_json(silent=True) or {}

        message = str(data.get("message", "")).strip()

        if not message:
            return jsonify({
                "error": "Please enter a construction question."
            }), 400

        if len(message) > 5000:
            return jsonify({
                "error": "Question must be under 5000 characters."
            }), 400

        print("Using Gemini model:", MODEL_NAME, flush=True)

        answer = None

        # Retry temporary server errors.
        for attempt in range(3):

            try:
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=message,
                    config={
                        "system_instruction": (
                            "You are BuildNest AI, a helpful house "
                            "construction and budgeting assistant. "
                            "Answer questions about house construction, "
                            "cement, steel, bricks, sand, labour, "
                            "building materials and budgeting. "
                            "Use simple English and clear points. "
                            "Give approximate Indian Rupee estimates "
                            "when appropriate. Explain cost-saving "
                            "methods. Mention that actual costs vary "
                            "by location and design. Recommend consulting "
                            "a qualified engineer or architect for "
                            "structural advice."
                        ),
                        "temperature": 0.5,
                        "max_output_tokens": 1000
                    }
                )

                answer = response.text

                if answer:
                    break

                raise RuntimeError("Gemini returned an empty response.")

            except Exception as e:

                error_text = str(e).upper()

                temporary_error = (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text
                    or "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                )

                if temporary_error and attempt < 2:

                    wait_time = 3 * (attempt + 1)

                    print(
                        f"Gemini temporarily unavailable. "
                        f"Retrying in {wait_time} seconds...",
                        flush=True
                    )

                    time.sleep(wait_time)

                else:
                    raise

        if not answer:
            return jsonify({
                "error": "Gemini did not return an answer. Try again."
            }), 502

        print("Gemini response received successfully!", flush=True)

        return jsonify({
            "reply": answer
        }), 200

    except Exception as e:

        error_message = str(e)
        error_upper = error_message.upper()

        print("GEMINI API ERROR:", error_message, flush=True)

        if "429" in error_upper or "RESOURCE_EXHAUSTED" in error_upper:
            return jsonify({
                "error": "Gemini API quota reached. Please try later."
            }), 429

        if "503" in error_upper or "UNAVAILABLE" in error_upper:
            return jsonify({
                "error": "Gemini is temporarily busy. Please try again."
            }), 503

        if "API_KEY_INVALID" in error_upper or "API KEY NOT VALID" in error_upper:
            return jsonify({
                "error": "Invalid Gemini API key. Check your .env file."
            }), 401

        return jsonify({
            "error": "Unable to get an AI response. Please try again.",
            "details": error_message[:300]
        }), 500


# =====================================
# 7. HEALTH CHECK
# =====================================

@app.route("/health")
def health():

    return jsonify({
        "status": "running",
        "gemini_configured": client is not None,
        "model": MODEL_NAME
    })


# =====================================
# 8. RUN FLASK APPLICATION
# =====================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
