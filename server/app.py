from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

import requests
import time
import os
import sqlite3
import tempfile
import urllib.parse

from datetime import datetime

from pdf_rag import extract_text_from_pdf, chunk_text
import rag


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-3.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
)

DATABASE = "marketmate.db"


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module TEXT,
            input_text TEXT,
            output_text TEXT,
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            platform TEXT,
            scheduled_date TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================================================
# HISTORY
# =========================================================

def save_history(module, input_text, output_text):
    try:
        conn = get_db()

        conn.execute(
            """
            INSERT INTO history
            (module, input_text, output_text, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                module,
                input_text,
                output_text,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        conn.commit()
        conn.close()

    except Exception as e:
        print("History error:", e)


# =========================================================
# GEMINI
# =========================================================

def call_gemini(prompt, timeout=30):

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

    for attempt in range(3):

        try:

            response = requests.post(
                GEMINI_URL,
                json=payload,
                timeout=timeout
            )

            result = response.json()

            if response.status_code == 200:

                candidates = result.get("candidates", [])

                if candidates:

                    content = candidates[0].get(
                        "content",
                        {}
                    )

                    parts = content.get(
                        "parts",
                        []
                    )

                    if parts:
                        return parts[0].get(
                            "text",
                            ""
                        )

                return ""

            if response.status_code in [
                429,
                500,
                502,
                503,
                504
            ]:

                if attempt < 2:
                    time.sleep(3)
                    continue

            print("Gemini error:", result)

            return None

        except requests.exceptions.RequestException as e:

            print("Gemini request error:", e)

            if attempt < 2:
                time.sleep(3)
                continue

    return None


# =========================================================
# CONTEXT FROM RAG
# =========================================================

def get_marketing_context(query):

    try:
        return rag.get_combined_context(
            query,
            csv_top_k=2,
            pdf_top_k=3
        )

    except Exception as e:

        print("RAG error:", e)

        return ""


# =========================================================
# HEALTH
# =========================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "message": "AI Marketing SaaS Backend Server is running!"
    })


# =========================================================
# PDF UPLOAD
# =========================================================

@app.route("/api/upload-pdf", methods=["POST"])
def upload_pdf():

    try:

        if "file" not in request.files:

            return jsonify({
                "error": "No PDF file uploaded"
            }), 400

        file = request.files["file"]

        if file.filename == "":

            return jsonify({
                "error": "No file selected"
            }), 400

        if not file.filename.lower().endswith(".pdf"):

            return jsonify({
                "error": "Only PDF files are allowed"
            }), 400

        temp_path = None

        try:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf"
            ) as temp_file:

                temp_path = temp_file.name

                file.save(temp_path)

            # Extract PDF text
            text = extract_text_from_pdf(
                temp_path
            )

            if not text.strip():

                return jsonify({
                    "error": "Could not extract text from PDF"
                }), 400

            # Create chunks
            chunks = chunk_text(
                text,
                chunk_size=1000
            )

            # Store chunks in RAG memory
            rag.set_pdf_chunks(chunks)

            return jsonify({

                "message":
                    "PDF uploaded and processed successfully",

                "filename":
                    file.filename,

                "text_length":
                    len(text),

                "chunks":
                    len(chunks)

            }), 200

        finally:

            if (
                temp_path
                and os.path.exists(temp_path)
            ):

                os.remove(temp_path)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# PDF STATUS
# =========================================================

@app.route("/api/pdf-status", methods=["GET"])
def pdf_status():

    try:

        count = rag.get_pdf_chunk_count()

        return jsonify({

            "pdf_loaded":
                count > 0,

            "chunks":
                count

        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# CLEAR PDF
# =========================================================

@app.route("/api/clear-pdf", methods=["POST"])
def clear_pdf():

    try:

        rag.clear_pdf_chunks()

        return jsonify({

            "message":
                "PDF knowledge cleared successfully",

            "chunks":
                0

        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# CAPTION
# =========================================================

@app.route("/api/generate-caption", methods=["POST"])
def generate_caption():

    try:

        data = request.get_json() or {}

        topic = data.get(
            "topic",
            ""
        )

        tone = data.get(
            "tone",
            "Professional"
        )

        platform = data.get(
            "platform",
            "Instagram"
        )

        if not topic:

            return jsonify({
                "error": "Topic is required"
            }), 400

        query = (
            f"{topic} "
            f"{tone} "
            f"{platform}"
        )

        context = get_marketing_context(
            query
        )

        prompt = f"""
You are an expert social media marketing assistant.

Create a social media caption.

Topic: {topic}
Tone: {tone}
Platform: {platform}

Use the following retrieved marketing
knowledge when relevant:

{context}

Requirements:
- Keep it concise and engaging.
- Make it suitable for the selected platform.
- Use the requested tone.
- Do not include hashtags.
"""

        caption = call_gemini(prompt)

        if caption is None:

            return jsonify({
                "error": "Gemini API request failed"
            }), 500

        save_history(
            "caption",
            topic,
            caption
        )

        return jsonify({
            "caption": caption
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# AD COPY
# =========================================================

@app.route("/api/generate-ad-copy", methods=["POST"])
def generate_ad_copy():

    try:

        data = request.get_json() or {}

        product = data.get(
            "product",
            ""
        )

        target_audience = data.get(
            "target_audience",
            ""
        )

        tone = data.get(
            "tone",
            "Professional"
        )

        platform = data.get(
            "platform",
            "Instagram"
        )

        if not product:

            return jsonify({
                "error": "Product is required"
            }), 400

        query = (
            f"{product} "
            f"{target_audience} "
            f"{tone} "
            f"{platform}"
        )

        context = get_marketing_context(
            query
        )

        prompt = f"""
Create marketing ad copy.

Product: {product}
Target Audience: {target_audience}
Tone: {tone}
Platform: {platform}

Retrieved marketing knowledge:

{context}

Create multiple ad variations.

Each ad should have:
- Headline under 8 words
- Description under 20 words

Format clearly with numbering.
"""

        ad_copy = call_gemini(prompt)

        if ad_copy is None:

            return jsonify({
                "error": "Gemini API request failed"
            }), 500

        save_history(
            "ad-copy",
            product,
            ad_copy
        )

        return jsonify({
            "ad_copy": ad_copy
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# PRODUCT DESCRIPTION
# =========================================================

@app.route(
    "/api/generate-product-description",
    methods=["POST"]
)
def generate_product_description():

    try:

        data = request.get_json() or {}

        product_name = data.get(
            "product_name",
            ""
        )

        features = data.get(
            "features",
            ""
        )

        tone = data.get(
            "tone",
            "Professional"
        )

        if not product_name:

            return jsonify({
                "error": "Product name is required"
            }), 400

        query = (
            f"{product_name} "
            f"{features} "
            f"{tone}"
        )

        context = get_marketing_context(
            query
        )

        prompt = f"""
Write a product description.

Product Name:
{product_name}

Features:
{features}

Tone:
{tone}

Retrieved marketing knowledge:

{context}

Make the description persuasive.
Highlight customer benefits, not only features.
Keep it around 100 words.
Include a short catchy opening line.
"""

        description = call_gemini(
            prompt
        )

        if description is None:

            return jsonify({
                "error": "Gemini API request failed"
            }), 500

        save_history(
            "product-description",
            product_name,
            description
        )

        return jsonify({
            "description": description
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# SLOGAN
# =========================================================

@app.route(
    "/api/generate-slogan",
    methods=["POST"]
)
def generate_slogan():

    try:

        data = request.get_json() or {}

        business_name = data.get(
            "business_name",
            ""
        )

        tone = data.get(
            "tone",
            "Catchy"
        )

        if not business_name:

            return jsonify({
                "error": "Business name is required"
            }), 400

        query = (
            f"{business_name} "
            f"{tone}"
        )

        context = get_marketing_context(
            query
        )

        prompt = f"""
Generate catchy marketing slogans.

Business Name:
{business_name}

Tone:
{tone}

Retrieved marketing knowledge:

{context}

Keep each slogan under 8 words.
Make them short, punchy and brandable.
Return a numbered list.
"""

        slogans = call_gemini(
            prompt
        )

        if slogans is None:

            return jsonify({
                "error": "Gemini API request failed"
            }), 500

        save_history(
            "slogan",
            business_name,
            slogans
        )

        return jsonify({
            "slogans": slogans
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# HASHTAGS
# =========================================================

@app.route(
    "/api/generate-hashtags",
    methods=["POST"]
)
def generate_hashtags():

    try:

        data = request.get_json() or {}

        topic = data.get(
            "topic",
            ""
        )

        platform = data.get(
            "platform",
            "Instagram"
        )

        if not topic:

            return jsonify({
                "error": "Topic is required"
            }), 400

        query = (
            f"{topic} "
            f"{platform}"
        )

        context = get_marketing_context(
            query
        )

        prompt = f"""
Generate relevant hashtags.

Topic:
{topic}

Platform:
{platform}

Retrieved marketing knowledge:

{context}

Return ONLY hashtags separated by spaces.
Do not add explanations.
"""

        hashtags = call_gemini(
            prompt
        )

        if hashtags is None:

            return jsonify({
                "error": "Gemini API request failed"
            }), 500

        save_history(
            "hashtags",
            topic,
            hashtags
        )

        return jsonify({
            "hashtags": hashtags
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# SEO
# =========================================================

@app.route(
    "/api/generate-seo",
    methods=["POST"]
)
def generate_seo():

    try:

        data = request.get_json() or {}

        topic = data.get(
            "topic",
            ""
        )

        keyword = data.get(
            "keyword",
            ""
        )

        if not topic:

            return jsonify({
                "error": "Topic is required"
            }), 400

        query = (
            f"{topic} "
            f"{keyword}"
        )

        context = get_marketing_context(
            query
        )

        prompt = f"""
You are an SEO content expert.

Topic:
{topic}

Target Keyword:
{keyword}

Retrieved marketing knowledge:

{context}

Create SEO-friendly content including:
- SEO Title
- Meta Description
- Keywords
- Short optimized content
"""

        seo_content = call_gemini(
            prompt
        )

        if seo_content is None:

            return jsonify({
                "error": "Gemini API request failed"
            }), 500

        save_history(
            "seo",
            topic,
            seo_content
        )

        return jsonify({
            "seo_content": seo_content
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# EMAIL
# =========================================================

@app.route(
    "/api/generate-email",
    methods=["POST"]
)
def generate_email():

    try:

        data = request.get_json() or {}

        purpose = data.get(
            "purpose",
            ""
        )

        product = data.get(
            "product",
            ""
        )

        tone = data.get(
            "tone",
            "Professional"
        )

        if not purpose or not product:

            return jsonify({
                "error":
                    "Purpose and product are required"
            }), 400

        query = (
            f"{purpose} "
            f"{product} "
            f"{tone}"
        )

        context = get_marketing_context(
            query
        )

        prompt = f"""
Create a professional marketing email.

Purpose:
{purpose}

Product:
{product}

Tone:
{tone}

Retrieved marketing knowledge:

{context}

Return:

Subject:
Email Body:

Make it clear, persuasive and professional.
"""

        email_content = call_gemini(
            prompt
        )

        if email_content is None:

            return jsonify({
                "error": "Gemini API request failed"
            }), 500

        save_history(
            "email",
            product,
            email_content
        )

        return jsonify({
            "email": email_content
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# COMPETITOR ANALYSIS
# =========================================================

@app.route(
    "/api/competitor-analysis",
    methods=["POST"]
)
def competitor_analysis():

    try:

        data = request.get_json() or {}

        business = data.get(
            "business",
            ""
        )

        competitor = data.get(
            "competitor",
            ""
        )

        if not business or not competitor:

            return jsonify({
                "error":
                    "Business and competitor are required"
            }), 400

        query = (
            f"{business} "
            f"{competitor}"
        )

        context = get_marketing_context(
            query
        )

        prompt = f"""
Perform a marketing competitor analysis.

Business:
{business}

Competitor:
{competitor}

Retrieved marketing knowledge:

{context}

Provide:

1. Strengths
2. Weaknesses
3. Marketing Strategy
4. Target Audience
5. Opportunities
6. Recommendations

Keep it concise and useful.
"""

        analysis = call_gemini(
            prompt
        )

        if analysis is None:

            return jsonify({
                "error": "Gemini API request failed"
            }), 500

        save_history(
            "competitor",
            business,
            analysis
        )

        return jsonify({
            "analysis": analysis
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# IMAGE
# =========================================================

@app.route(
    "/api/generate-image",
    methods=["POST"]
)
def generate_image():

    try:

        data = request.get_json() or {}

        prompt = data.get(
            "prompt",
            ""
        )

        if not prompt:

            return jsonify({
                "error": "Prompt is required"
            }), 400

        image_url = (
            "https://image.pollinations.ai/prompt/"
            + urllib.parse.quote(prompt)
        )

        return jsonify({
            "image_url": image_url
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# LANDING PAGE
# =========================================================

@app.route(
    "/api/generate-landing-page",
    methods=["POST"]
)
def generate_landing_page():

    try:

        data = request.get_json() or {}

        business_name = data.get(
            "business_name",
            ""
        )

        description = data.get(
            "description",
            ""
        )

        if not business_name:

            return jsonify({
                "error":
                    "Business name is required"
            }), 400

        query = (
            f"{business_name} "
            f"{description}"
        )

        context = get_marketing_context(
            query
        )

        prompt = f"""
Create a complete responsive landing page in HTML.

Business Name:
{business_name}

Description:
{description}

Retrieved marketing knowledge:

{context}

Requirements:
- Modern design
- Clear hero section
- Product/service benefits
- Call-to-action
- Responsive layout
- Attractive marketing copy

Return ONLY the raw HTML code
starting with <!DOCTYPE html>.

Do not use markdown code fences.
Do not add explanations.
"""

        html_content = call_gemini(
            prompt
        )

        if html_content is None:

            return jsonify({
                "error": "Gemini API request failed"
            }), 500

        save_history(
            "landing",
            business_name,
            html_content[:200]
        )

        return jsonify({
            "html_content": html_content
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# SCHEDULER
# =========================================================

@app.route(
    "/api/schedule-post",
    methods=["POST"]
)
def schedule_post():

    try:

        data = request.get_json() or {}

        content = data.get(
            "content",
            ""
        )

        platform = data.get(
            "platform",
            ""
        )

        scheduled_date = data.get(
            "scheduled_date",
            ""
        )

        if not content:

            return jsonify({
                "error":
                    "Content is required"
            }), 400

        conn = get_db()

        cursor = conn.execute(
            """
            INSERT INTO scheduled_posts
            (content, platform, scheduled_date, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                content,
                platform,
                scheduled_date,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
        )

        conn.commit()

        post_id = cursor.lastrowid

        conn.close()

        return jsonify({

            "message":
                "Post scheduled successfully",

            "id":
                post_id

        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# SCHEDULED POSTS
# =========================================================

@app.route(
    "/api/scheduled-posts",
    methods=["GET"]
)
def scheduled_posts():

    try:

        conn = get_db()

        rows = conn.execute(
            """
            SELECT *
            FROM scheduled_posts
            ORDER BY id DESC
            """
        ).fetchall()

        conn.close()

        posts = [
            dict(row)
            for row in rows
        ]

        return jsonify(posts)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# HISTORY
# =========================================================

@app.route(
    "/api/history",
    methods=["GET"]
)
def history():

    try:

        conn = get_db()

        rows = conn.execute(
            """
            SELECT *
            FROM history
            ORDER BY id DESC
            """
        ).fetchall()

        conn.close()

        return jsonify([
            dict(row)
            for row in rows
        ])

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# ANALYTICS
# =========================================================

@app.route(
    "/api/analytics",
    methods=["GET"]
)
def analytics():

    try:

        conn = get_db()

        total_content = conn.execute(
            """
            SELECT COUNT(*)
            FROM history
            """
        ).fetchone()[0]

        total_scheduled = conn.execute(
            """
            SELECT COUNT(*)
            FROM scheduled_posts
            """
        ).fetchone()[0]

        module_rows = conn.execute(
            """
            SELECT module, COUNT(*) as count
            FROM history
            GROUP BY module
            """
        ).fetchall()

        conn.close()

        module_usage = {
            row["module"]:
                row["count"]
            for row in module_rows
        }

        return jsonify({

            "total_content":
                total_content,

            "total_scheduled":
                total_scheduled,

            "module_usage":
                module_usage

        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )