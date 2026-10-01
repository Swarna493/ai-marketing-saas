from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os

from rag import retrieve_context

load_dotenv()

app = Flask(__name__)
CORS(app)

# ==============================
# Gemini API Configuration
# ==============================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key="
    + (GEMINI_API_KEY or "")
)


# ==============================
# Health Check
# ==============================

@app.route('/api/health', methods=['GET'])
def health_check():

    return jsonify({
        "status": "Server is running!",
        "message": "AI Marketing SaaS Backend"
    })


# ==============================
# Generate Caption
# ==============================

@app.route('/api/generate-caption', methods=['POST'])
def generate_caption():

    try:

        # Get request data
        data = request.get_json(silent=True) or {}

        topic = data.get('topic', '')
        tone = data.get('tone', 'engaging')
        platform = data.get('platform', 'Instagram')

        # Check topic
        if not topic:
            return jsonify({
                "error": "Topic is required"
            }), 400

        # Check API key
        if not GEMINI_API_KEY:
            return jsonify({
                "error": "GEMINI_API_KEY is not configured on the server"
            }), 500

        # ==============================
        # RAG RETRIEVAL
        # ==============================

        query = f"{topic} {tone} {platform}"

        retrieved_results = retrieve_context(
            query,
            top_k=3
        )

        # Create RAG context
        rag_context = "\n\n".join([
            f"""
Product: {item.get('product', '')}
Description: {item.get('description', '')}
Target Audience: {item.get('target_audience', '')}
Platform: {item.get('platform', '')}
Tone: {item.get('tone', '')}
Keywords: {item.get('keywords', '')}
"""
            for item in retrieved_results
        ])

        # If no dataset results
        if not rag_context:
            rag_context = "No specific marketing information was found in the dataset."


        # ==============================
        # GEMINI PROMPT
        # ==============================

        prompt = f"""
Write a {tone} social media caption for {platform} about:

{topic}

Use the following relevant marketing information
retrieved from the marketing dataset:

{rag_context}

Create a natural and engaging caption.

Keep it concise and suitable for {platform}.

Do not include hashtags in this response.
"""


        # ==============================
        # GEMINI API PAYLOAD
        # ==============================

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


        # ==============================
        # GEMINI API REQUEST
        # ==============================

        response = requests.post(
            GEMINI_URL,
            json=payload,
            timeout=60
        )

        print("Gemini status:", response.status_code)
        print("Gemini response:", response.text)

        try:
            result = response.json()
        except ValueError:
            return jsonify({
                "error": "Gemini returned an invalid response",
                "response": response.text
            }), 500


        # ==============================
        # HANDLE GEMINI ERROR
        # ==============================

        if response.status_code != 200:

            return jsonify({
                "error": result
            }), response.status_code


        # ==============================
        # GET GENERATED CAPTION
        # ==============================

        candidates = result.get("candidates", [])

        if not candidates:
            return jsonify({
                "error": "Gemini did not return any generated content",
                "details": result
            }), 500

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        if not parts:
            return jsonify({
                "error": "Gemini response does not contain text",
                "details": result
            }), 500

        caption = parts[0].get("text", "")

        if not caption:
            return jsonify({
                "error": "Generated caption is empty"
            }), 500


        # ==============================
        # RETURN RESPONSE
        # ==============================

        return jsonify({
            "caption": caption,
            "rag_context": retrieved_results
        })


    # ==============================
    # GENERAL ERROR
    # ==============================

    except requests.exceptions.Timeout:

        return jsonify({
            "error": "Gemini API request timed out"
        }), 504

    except requests.exceptions.RequestException as e:

        return jsonify({
            "error": f"Gemini API request failed: {str(e)}"
        }), 500

    except Exception as e:

        print("Backend error:", str(e))

        return jsonify({
            "error": str(e)
        }), 500


# ==============================
# Run Flask Server
# ==============================

if __name__ == '__main__':

    app.run(
        host="0.0.0.0",
        port=5000
    )