from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os
import sqlite3

from rag import retrieve_context

load_dotenv()

app = Flask(__name__)
CORS(app)

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key="
    + GEMINI_API_KEY
)


@app.route('/api/health', methods=['GET'])
def health_check():

    return jsonify({
        "status": "Server is running!",
        "message": "AI Marketing SaaS Backend"
    })


@app.route('/api/generate-caption', methods=['POST'])
def generate_caption():

    try:

        data = request.get_json()

        topic = data.get('topic', '')
        tone = data.get('tone', 'engaging')
        platform = data.get('platform', 'Instagram')

        if not topic:
            return jsonify({
                "error": "Topic is required"
            }), 400

        # -----------------------------
        # RAG RETRIEVAL
        # -----------------------------

        query = f"{topic} {tone} {platform}"

        retrieved_results = retrieve_context(
            query,
            top_k=3
        )

        # Create context from retrieved dataset
        rag_context = "\n\n".join([
            f"""
Product: {item['product']}
Description: {item['description']}
Target Audience: {item['target_audience']}
Platform: {item['platform']}
Tone: {item['tone']}
Keywords: {item['keywords']}
"""
            for item in retrieved_results
        ])

        # -----------------------------
        # GEMINI PROMPT
        # -----------------------------

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

        # -----------------------------
        # GEMINI API REQUEST
        # -----------------------------

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

        response = requests.post(
            GEMINI_URL,
            json=payload
        )

        result = response.json()

        if response.status_code != 200:

            return jsonify({
                "error": result
            }), response.status_code

        # -----------------------------
        # GET GENERATED CAPTION
        # -----------------------------

        caption = result[
            'candidates'
        ][0][
            'content'
        ][
            'parts'
        ][0][
            'text'
        ]

        # -----------------------------
        # RETURN RESPONSE
        # -----------------------------

        return jsonify({
            "caption": caption,
            "rag_context": retrieved_results
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


if __name__ == '__main__':

    app.run(
        host="0.0.0.0",
        port=5000
    )