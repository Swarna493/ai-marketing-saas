from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os
import time

from rag import retrieve_context

load_dotenv()

app = Flask(__name__)
CORS(app)


# ==========================================
# Gemini API Configuration
# ==========================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3.8-flash:generateContent"
)


# ==========================================
# Health Check
# ==========================================

@app.route("/api/health", methods=["GET"])
def health_check():

    return jsonify({
        "status": "Server is running!",
        "message": "AI Marketing SaaS Backend"
    })


# ==========================================
# Generate Caption
# ==========================================

@app.route("/api/generate-caption", methods=["POST"])
def generate_caption():

    try:

        # --------------------------------------
        # Get request data
        # --------------------------------------

        data = request.get_json(silent=True) or {}

        topic = data.get("topic", "").strip()
        tone = data.get("tone", "engaging")
        platform = data.get("platform", "Instagram")


        # --------------------------------------
        # Validate topic
        # --------------------------------------

        if not topic:

            return jsonify({
                "error": "Topic is required",
                "message": "Please enter a topic before generating content."
            }), 400


        # --------------------------------------
        # Check Gemini API key
        # --------------------------------------

        if not GEMINI_API_KEY:

            return jsonify({
                "error": "GEMINI_API_KEY is not configured",
                "message": "Gemini API key is missing on the server."
            }), 500


        # ======================================
        # RAG RETRIEVAL
        # ======================================

        query = f"{topic} {tone} {platform}"

        retrieved_results = retrieve_context(
            query,
            top_k=3
        )


        # ======================================
        # CREATE RAG CONTEXT
        # ======================================

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
                "No specific marketing information was found "
                "in the dataset."
            )


        # ======================================
        # GEMINI PROMPT
        # ======================================

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
6. Do not mention the dataset or RAG.
"""


        # ======================================
        # GEMINI REQUEST PAYLOAD
        # ======================================

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


        # ======================================
        # AUTOMATIC RETRY
        # ======================================

        max_retries = 3

        response = None

        for attempt in range(max_retries):

            try:

                print(
                    f"Gemini request attempt "
                    f"{attempt + 1}/{max_retries}"
                )

                response = requests.post(
                    GEMINI_URL,
                    headers={
                        "x-goog-api-key": GEMINI_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=60
                )


                print(
                    "Gemini status:",
                    response.status_code
                )


                # ----------------------------------
                # Gemini temporarily unavailable
                # ----------------------------------

                if response.status_code == 503:

                    if attempt < max_retries - 1:

                        wait_time = 3 * (attempt + 1)

                        print(
                            f"Gemini is busy. "
                            f"Retrying in {wait_time} seconds..."
                        )

                        time.sleep(wait_time)

                        continue

                    else:

                        return jsonify({
                            "error": "Gemini service temporarily unavailable",
                            "message": (
                                "Gemini is currently experiencing "
                                "high demand. Please try again "
                                "in a few minutes."
                            )
                        }), 503


                # ----------------------------------
                # Other Gemini errors
                # ----------------------------------

                if response.status_code != 200:

                    try:
                        error_data = response.json()
                    except ValueError:
                        error_data = response.text

                    print(
                        "Gemini error:",
                        error_data
                    )

                    return jsonify({
                        "error": "Gemini API request failed",
                        "details": error_data
                    }), response.status_code


                # ----------------------------------
                # Successful response
                # ----------------------------------

                break


            except requests.exceptions.Timeout:

                print(
                    f"Gemini request timed out "
                    f"on attempt {attempt + 1}"
                )

                if attempt < max_retries - 1:

                    wait_time = 3 * (attempt + 1)

                    time.sleep(wait_time)

                    continue

                return jsonify({
                    "error": "Gemini API timeout",
                    "message": (
                        "Gemini took too long to respond. "
                        "Please try again."
                    )
                }), 504


            except requests.exceptions.RequestException as e:

                print(
                    "Gemini request error:",
                    str(e)
                )

                return jsonify({
                    "error": "Gemini API request failed",
                    "message": str(e)
                }), 500


        # ======================================
        # READ GEMINI RESPONSE
        # ======================================

        try:

            result = response.json()

        except ValueError:

            return jsonify({
                "error": "Invalid Gemini response",
                "message": (
                    "Gemini returned a response that "
                    "could not be read."
                )
            }), 500


        # ======================================
        # GET CANDIDATES
        # ======================================

        candidates = result.get(
            "candidates",
            []
        )


        if not candidates:

            return jsonify({
                "error": "No generated content",
                "message": (
                    "Gemini did not return any generated content."
                ),
                "details": result
            }), 500


        # ======================================
        # GET CONTENT
        # ======================================

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


        # ======================================
        # GET CAPTION
        # ======================================

        caption = parts[0].get(
            "text",
            ""
        )


        if not caption:

            return jsonify({
                "error": "Generated caption is empty",
                "message": (
                    "Gemini generated an empty response."
                )
            }), 500


        # ======================================
        # SUCCESS RESPONSE
        # ======================================

        return jsonify({
            "caption": caption,
            "rag_context": retrieved_results
        }), 200


    # ==========================================
    # GENERAL ERROR
    # ==========================================

    except Exception as e:

        print(
            "Backend error:",
            str(e)
        )

        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


# ==========================================
# Run Flask Server
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )