from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os

from rag import retrieve_context

load_dotenv()

app = Flask(__name__)
CORS(app)

# Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Stable Gemini models
# The backend will try them in this order.
GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash"
]


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health_check():

    return jsonify({
        "status": "Server is running!",
        "message": "AI Marketing SaaS Backend"
    })


# ---------------------------------------------------------
# GENERATE CAPTION
# ---------------------------------------------------------

@app.route("/api/generate-caption", methods=["POST"])
def generate_caption():

    try:

        # -------------------------------------------------
        # Read user input
        # -------------------------------------------------

        data = request.get_json(silent=True) or {}

        topic = data.get("topic", "").strip()
        tone = data.get("tone", "engaging")
        platform = data.get("platform", "Instagram")

        # -------------------------------------------------
        # Validate topic
        # -------------------------------------------------

        if not topic:

            return jsonify({
                "error": "Topic is required",
                "message": (
                    "Please enter a topic before "
                    "generating content."
                )
            }), 400

        # -------------------------------------------------
        # Check Gemini API key
        # -------------------------------------------------

        if not GEMINI_API_KEY:

            return jsonify({
                "error": "GEMINI_API_KEY is not configured",
                "message": (
                    "Gemini API key is missing "
                    "on the server."
                )
            }), 500

        # -------------------------------------------------
        # RAG RETRIEVAL
        # -------------------------------------------------

        query = f"{topic} {tone} {platform}"

        retrieved_results = retrieve_context(
            query,
            top_k=3
        )

        # -------------------------------------------------
        # Prepare RAG context
        # -------------------------------------------------

        rag_context = "\n\n".join([
            f"""
Product: {item.get("product", "")}
Description: {item.get("description", "")}
Target Audience: {item.get("target_audience", "")}
Platform: {item.get("platform", "")}
Tone: {item.get("tone", "")}
Keywords: {item.get("keywords", "")}
Brand Style: {item.get("brand_style", "")}
"""
            for item in retrieved_results
        ])

        if not rag_context:

            rag_context = (
                "No specific marketing information "
                "was found in the dataset."
            )

        # -------------------------------------------------
        # PROMPT
        # -------------------------------------------------

        prompt = f"""
You are an AI marketing assistant.

Write a {tone} social media caption for {platform}.

Topic:
{topic}

Use the following relevant marketing information
retrieved from the marketing dataset:

{rag_context}

Requirements:

1. Create a natural and engaging caption.
2. Keep it concise.
3. Make it suitable for {platform}.
4. Use the retrieved information when relevant.
5. Do not include hashtags.
6. Do not mention the dataset.
7. Do not mention RAG.
"""

        # -------------------------------------------------
        # GEMINI REQUEST PAYLOAD
        # -------------------------------------------------

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        # -------------------------------------------------
        # TRY GEMINI MODELS
        # -------------------------------------------------

        response = None
        last_error = None

        for model in GEMINI_MODELS:

            gemini_url = (
                "https://generativelanguage.googleapis.com/"
                "v1beta/models/"
                f"{model}:generateContent"
            )

            try:

                print(
                    f"Gemini request using model: {model}"
                )

                response = requests.post(
                    gemini_url,
                    headers={
                        "x-goog-api-key": GEMINI_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=8
                )

                print(
                    f"Gemini model {model} "
                    f"returned status: "
                    f"{response.status_code}"
                )

                # -------------------------------------------------
                # SUCCESS
                # -------------------------------------------------

                if response.status_code == 200:

                    print(
                        f"Gemini model {model} "
                        f"worked successfully."
                    )

                    break

                # -------------------------------------------------
                # TEMPORARY ERROR
                # Try next model
                # -------------------------------------------------

                if response.status_code in [429, 503]:

                    last_error = response.text

                    print(
                        f"Gemini model {model} "
                        f"is temporarily unavailable."
                    )

                    print(
                        "Trying the next Gemini model..."
                    )

                    continue

                # -------------------------------------------------
                # OTHER GEMINI ERROR
                # -------------------------------------------------

                try:

                    error_data = response.json()

                except ValueError:

                    error_data = response.text

                print(
                    "Gemini API error:",
                    error_data
                )

                return jsonify({
                    "error": "Gemini API request failed",
                    "details": error_data
                }), response.status_code

            # -----------------------------------------------------
            # TIMEOUT
            # -----------------------------------------------------

            except requests.exceptions.Timeout:

                last_error = (
                    f"{model} request timed out."
                )

                print(
                    f"Gemini model {model} "
                    "timed out."
                )

                print(
                    "Trying the next Gemini model..."
                )

                continue

            # -----------------------------------------------------
            # REQUEST ERROR
            # -----------------------------------------------------

            except requests.exceptions.RequestException as e:

                last_error = str(e)

                print(
                    f"Gemini request error "
                    f"with {model}: {e}"
                )

                print(
                    "Trying the next Gemini model..."
                )

                continue

        # ---------------------------------------------------------
        # ALL MODELS FAILED
        # ---------------------------------------------------------

        if response is None or response.status_code != 200:

            return jsonify({
                "error": (
                    "Gemini service temporarily unavailable"
                ),
                "message": (
                    "All available Gemini models are "
                    "currently busy or unavailable. "
                    "Please try again."
                ),
                "details": last_error
            }), 503

        # ---------------------------------------------------------
        # READ GEMINI RESPONSE
        # ---------------------------------------------------------

        try:

            result = response.json()

        except ValueError:

            return jsonify({
                "error": "Invalid Gemini response",
                "message": (
                    "Gemini returned a response "
                    "that could not be read."
                )
            }), 500

        # ---------------------------------------------------------
        # CHECK CANDIDATES
        # ---------------------------------------------------------

        candidates = result.get(
            "candidates",
            []
        )

        if not candidates:

            return jsonify({
                "error": "No generated content",
                "message": (
                    "Gemini did not return "
                    "any generated content."
                ),
                "details": result
            }), 500

        # ---------------------------------------------------------
        # GET CONTENT
        # ---------------------------------------------------------

        content = candidates[0].get(
            "content",
            {}
        )

        parts = content.get(
            "parts",
            []
        )

        if not parts:

            return jsonify({
                "error": "Empty Gemini response",
                "message": (
                    "Gemini returned no text content."
                ),
                "details": result
            }), 500

        # ---------------------------------------------------------
        # GET CAPTION
        # ---------------------------------------------------------

        caption = parts[0].get(
            "text",
            ""
        )

        if not caption:

            return jsonify({
                "error": "Generated caption is empty",
                "message": (
                    "Gemini generated "
                    "an empty response."
                )
            }), 500

        # ---------------------------------------------------------
        # SUCCESS RESPONSE
        # ---------------------------------------------------------

        return jsonify({
            "caption": caption,
            "rag_context": retrieved_results
        }), 200

    # -------------------------------------------------------------
    # GENERAL BACKEND ERROR
    # -------------------------------------------------------------

    except Exception as e:

        print(
            "Backend error:",
            str(e)
        )

        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


# ---------------------------------------------------------
# RUN LOCAL SERVER
# ---------------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )