from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os
import sqlite3
import urllib.parse
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"

DB_NAME = "marketmate.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            input_text TEXT NOT NULL,
            output_text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            platform TEXT NOT NULL,
            scheduled_date TEXT NOT NULL,
            status TEXT DEFAULT 'scheduled',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_history(item_type, input_text, output_text):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO history (type, input_text, output_text, created_at) VALUES (?, ?, ?, ?)",
        (item_type, input_text, output_text, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


init_db()


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "Server is running!", "message": "AI Marketing SaaS Backend"})


@app.route('/api/generate-caption', methods=['POST'])
def generate_caption():
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        tone = data.get('tone', 'engaging')
        platform = data.get('platform', 'Instagram')
        if not topic:
            return jsonify({"error": "Topic is required"}), 400
        prompt = f"""Write a {tone} social media caption for {platform} about: {topic}
Keep it concise, engaging, and suitable for the platform. Do not include hashtags in this response."""
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(GEMINI_URL, json=payload)
        result = response.json()
        if response.status_code != 200:
            return jsonify({"error": result}), response.status_code
        caption = result['candidates'][0]['content']['parts'][0]['text']
        save_history("caption", topic, caption)
        return jsonify({"caption": caption, "topic": topic, "tone": tone, "platform": platform})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate-hashtags', methods=['POST'])
def generate_hashtags():
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        if not topic:
            return jsonify({"error": "Topic is required"}), 400
        prompt = f"""Generate 15 relevant, trending social media hashtags for this topic: {topic}
Return ONLY the hashtags separated by spaces, nothing else. No numbering, no explanation."""
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(GEMINI_URL, json=payload)
        result = response.json()
        if response.status_code != 200:
            return jsonify({"error": result}), response.status_code
        hashtags = result['candidates'][0]['content']['parts'][0]['text']
        save_history("hashtag", topic, hashtags)
        return jsonify({"hashtags": hashtags, "topic": topic})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate-seo', methods=['POST'])
def generate_seo():
    try:
        data = request.get_json()
        keyword = data.get('keyword', '')
        if not keyword:
            return jsonify({"error": "Keyword is required"}), 400
        prompt = f"""Write an SEO-optimized blog title and a 100-word meta description for a business targeting this keyword: {keyword}
Format your response as:
Title: [title here]
Description: [description here]"""
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(GEMINI_URL, json=payload)
        result = response.json()
        if response.status_code != 200:
            return jsonify({"error": result}), response.status_code
        seo_content = result['candidates'][0]['content']['parts'][0]['text']
        save_history("seo", keyword, seo_content)
        return jsonify({"seo_content": seo_content, "keyword": keyword})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate-email', methods=['POST'])
def generate_email():
    try:
        data = request.get_json()
        purpose = data.get('purpose', '')
        product = data.get('product', '')
        if not purpose or not product:
            return jsonify({"error": "Purpose and product are required"}), 400
        prompt = f"""Write a professional marketing email for the following:
Purpose: {purpose}
Product/Service: {product}
Include a subject line and email body. Keep it concise, persuasive, and include a clear call-to-action.
Format your response as:
Subject: [subject line here]
Body: [email body here]"""
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(GEMINI_URL, json=payload)
        result = response.json()
        if response.status_code != 200:
            return jsonify({"error": result}), response.status_code
        email_content = result['candidates'][0]['content']['parts'][0]['text']
        save_history("email", f"{purpose} - {product}", email_content)
        return jsonify({"email_content": email_content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/competitor-analysis', methods=['POST'])
def competitor_analysis():
    try:
        data = request.get_json()
        business = data.get('business', '')
        competitor = data.get('competitor', '')
        if not business or not competitor:
            return jsonify({"error": "Business and competitor names are required"}), 400
        prompt = f"""Provide a brief competitive marketing analysis comparing these two businesses:
My Business: {business}
Competitor: {competitor}
Include: 1) Likely strengths of the competitor, 2) Potential opportunities for my business to differentiate, 3) One actionable marketing suggestion.
Keep it concise, under 150 words, formatted with clear sections."""
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(GEMINI_URL, json=payload)
        result = response.json()
        if response.status_code != 200:
            return jsonify({"error": result}), response.status_code
        analysis = result['candidates'][0]['content']['parts'][0]['text']
        save_history("competitor", f"{business} vs {competitor}", analysis)
        return jsonify({"analysis": analysis})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate-ad-copy', methods=['POST'])
def generate_ad_copy():
    try:
        data = request.get_json()
        product = data.get('product', '')
        platform = data.get('platform', 'Google Ads')
        if not product:
            return jsonify({"error": "Product is required"}), 400
        prompt = f"""Write 3 short, persuasive ad copy variations for {platform} advertising this product/service: {product}
Each ad should have a headline (under 8 words) and description (under 20 words). Format clearly with numbering."""
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(GEMINI_URL, json=payload)
        result = response.json()
        if response.status_code != 200:
            return jsonify({"error": result}), response.status_code
        ad_copy = result['candidates'][0]['content']['parts'][0]['text']
        save_history("adcopy", f"{product} - {platform}", ad_copy)
        return jsonify({"ad_copy": ad_copy})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate-product-description', methods=['POST'])
def generate_product_description():
    try:
        data = request.get_json()
        product_name = data.get('product_name', '')
        features = data.get('features', '')
        if not product_name:
            return jsonify({"error": "Product name is required"}), 400
        prompt = f"""Write a compelling e-commerce product description for: {product_name}
Key features/details: {features}
Make it persuasive, highlight benefits (not just features), and keep it around 100 words. Include a short catchy opening line."""
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(GEMINI_URL, json=payload)
        result = response.json()
        if response.status_code != 200:
            return jsonify({"error": result}), response.status_code
        description = result['candidates'][0]['content']['parts'][0]['text']
        save_history("productdesc", product_name, description)
        return jsonify({"description": description})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate-slogan', methods=['POST'])
def generate_slogan():
    try:
        data = request.get_json()
        business_name = data.get('business_name', '')
        industry = data.get('industry', '')
        if not business_name:
            return jsonify({"error": "Business name is required"}), 400
        prompt = f"""Generate 8 catchy, memorable slogans/taglines for this business:
Business Name: {business_name}
Industry: {industry}
Keep each slogan short (under 8 words), punchy, and brandable. Return as a numbered list."""
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(GEMINI_URL, json=payload)
        result = response.json()
        if response.status_code != 200:
            return jsonify({"error": result}), response.status_code
        slogans = result['candidates'][0]['content']['parts'][0]['text']
        save_history("slogan", business_name, slogans)
        return jsonify({"slogans": slogans})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM history ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()
        history = [dict(row) for row in rows]
        return jsonify({"history": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/schedule-post', methods=['POST'])
def schedule_post():
    try:
        data = request.get_json()
        content = data.get('content', '')
        platform = data.get('platform', 'Instagram')
        scheduled_date = data.get('scheduled_date', '')
        if not content or not scheduled_date:
            return jsonify({"error": "Content and date are required"}), 400
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO scheduled_posts (content, platform, scheduled_date, created_at) VALUES (?, ?, ?, ?)",
            (content, platform, scheduled_date, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Post scheduled successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scheduled-posts', methods=['GET'])
def get_scheduled_posts():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scheduled_posts ORDER BY scheduled_date ASC")
        rows = cursor.fetchall()
        conn.close()
        posts = [dict(row) for row in rows]
        return jsonify({"posts": posts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scheduled-posts/<int:post_id>', methods=['DELETE'])
def delete_scheduled_post(post_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scheduled_posts WHERE id = ?", (post_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Post deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT type, COUNT(*) FROM history GROUP BY type")
        type_counts = dict(cursor.fetchall())
        cursor.execute("SELECT COUNT(*) FROM history")
        total_generated = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM scheduled_posts")
        total_scheduled = cursor.fetchone()[0]
        conn.close()
        return jsonify({
            "total_generated": total_generated,
            "total_scheduled": total_scheduled,
            "breakdown": {
                "captions": type_counts.get("caption", 0),
                "hashtags": type_counts.get("hashtag", 0),
                "seo": type_counts.get("seo", 0),
                "emails": type_counts.get("email", 0),
                "competitor": type_counts.get("competitor", 0),
                "adcopy": type_counts.get("adcopy", 0),
                "productdesc": type_counts.get("productdesc", 0),
                "slogan": type_counts.get("slogan", 0)
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        if not prompt.strip():
            return jsonify({"error": "Prompt is required"}), 400
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true"
        save_history("image", prompt, image_url)
        return jsonify({"image_url": image_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate-landing-page', methods=['POST'])
def generate_landing_page():
    try:
        data = request.get_json()
        business_name = data.get('business_name', '')
        description = data.get('description', '')
        if not business_name or not description:
            return jsonify({"error": "Business name and description are required"}), 400
        prompt = f"""Create a complete, single-file HTML landing page for this business:
Business Name: {business_name}
Description: {description}
Requirements:
- Include all CSS inline in a style tag inside head
- Modern, clean design with a hero section, 3 feature/benefit highlights, and a call-to-action button
- Use a pleasant color scheme (purple/blue gradient theme)
- Make it mobile responsive
- Return ONLY the raw HTML code starting with DOCTYPE html, nothing else. No markdown code fences, no explanation."""
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(GEMINI_URL, json=payload)
        result = response.json()
        if response.status_code != 200:
            return jsonify({"error": result}), response.status_code
        html_content = result['candidates'][0]['content']['parts'][0]['text']
        html_content = html_content.replace('```html', '').replace('```', '').strip()
        save_history("landing", business_name, html_content[:200])
        return jsonify({"html_content": html_content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


app.run(host="0.0.0.0", port=5000)