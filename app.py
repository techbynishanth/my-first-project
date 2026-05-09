from flask import Flask, jsonify, request
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

load_dotenv()

app = Flask(__name__)
CORS(app, origins="*", allow_headers="*", methods=["GET", "POST", "OPTIONS"])

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

# Create database
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')

    # AI Tools table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            category TEXT,
            link TEXT,
            emoji TEXT
        )
    ''')

    # Favourites table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favourites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tool_id INTEGER
        )
    ''')

    # Insert AI tools if empty
    cursor.execute('SELECT COUNT(*) FROM tools')
    if cursor.fetchone()[0] == 0:
        tools = [
            # Image Generation
            ('Leonardo AI', 'Generate stunning AI images for free', 'Image Generation', 'https://leonardo.ai', '🎨'),
            ('Adobe Firefly', 'AI image generation by Adobe', 'Image Generation', 'https://firefly.adobe.com', '🔥'),
            ('Playground AI', 'Free AI image generator', 'Image Generation', 'https://playground.com', '🖼️'),

            # Video Editing
            ('Runway ML', 'AI video editing and generation', 'Video Editing', 'https://runwayml.com', '🎬'),
            ('CapCut', 'Free AI video editor', 'Video Editing', 'https://capcut.com', '✂️'),
            ('Pika Labs', 'Generate videos with AI', 'Video Editing', 'https://pika.art', '🎥'),

            # Animation
            ('D-ID', 'Create AI animated avatars', 'Animation', 'https://d-id.com', '🎭'),
            ('Kling AI', 'AI animation generator', 'Animation', 'https://klingai.com', '✨'),
            ('Animaker', 'Free AI animation maker', 'Animation', 'https://animaker.com', '🎪'),

            # PDF & Docs
            ('iLovePDF', 'Free PDF editor and converter', 'PDF & Docs', 'https://ilovepdf.com', '📄'),
            ('Smallpdf', 'All in one PDF tool', 'PDF & Docs', 'https://smallpdf.com', '📝'),
            ('PDF24', 'Free online PDF tools', 'PDF & Docs', 'https://pdf24.org', '🗂️'),

            # Writing & AI Chat
            ('ChatGPT', 'Most popular AI chatbot', 'Writing & Chat', 'https://chat.openai.com', '💬'),
            ('Claude', 'Anthropic AI assistant', 'Writing & Chat', 'https://claude.ai', '🤖'),
            ('Gemini', 'Google AI assistant', 'Writing & Chat', 'https://gemini.google.com', '♊'),

            # Audio & Music
            ('Suno AI', 'Generate music with AI', 'Audio & Music', 'https://suno.com', '🎵'),
            ('ElevenLabs', 'AI voice generation', 'Audio & Music', 'https://elevenlabs.io', '🎙️'),
            ('Mubert', 'AI music generator', 'Audio & Music', 'https://mubert.com', '🎶'),

            # Design
            ('Canva AI', 'AI powered design tool', 'Design', 'https://canva.com', '🎨'),
            ('Looka', 'AI logo maker', 'Design', 'https://looka.com', '💡'),
            ('Brandmark', 'AI brand identity maker', 'Design', 'https://brandmark.io', '🏷️'),

            # Coding
            ('GitHub Copilot', 'AI coding assistant', 'Coding', 'https://github.com/features/copilot', '💻'),
            ('Cursor', 'AI code editor', 'Coding', 'https://cursor.sh', '⌨️'),
            ('Replit AI', 'AI coding in browser', 'Coding', 'https://replit.com', '🖥️'),
        ]
        cursor.executemany('INSERT INTO tools (name, description, category, link, emoji) VALUES (?, ?, ?, ?, ?)', tools)

    conn.commit()
    conn.close()

# Get all tools
@app.route('/api/tools', methods=['GET'])
def get_tools():
    category = request.args.get('category', '')
    search = request.args.get('search', '')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if category and category != 'All':
        cursor.execute('SELECT * FROM tools WHERE category = ?', (category,))
    elif search:
        cursor.execute('SELECT * FROM tools WHERE name LIKE ? OR description LIKE ?',
                      (f'%{search}%', f'%{search}%'))
    else:
        cursor.execute('SELECT * FROM tools')

    tools = cursor.fetchall()
    conn.close()

    return jsonify([{
        'id': t[0], 'name': t[1], 'description': t[2],
        'category': t[3], 'link': t[4], 'emoji': t[5]
    } for t in tools])

# Signup
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    hashed_password = generate_password_hash(password)
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                      (name, email, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({ "message": "Account created successfully!" })
    except:
        return jsonify({ "error": "Email already exists!" }), 400

# Login
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        if user is None:
            return jsonify({ "error": "Email not found!" }), 401
        if check_password_hash(user[3], password):
            return jsonify({
                "message": "Login successful!",
                "user": { "id": user[0], "name": user[1], "email": user[2] }
            })
        else:
            return jsonify({ "error": "Wrong password!" }), 401
    except Exception as e:
        return jsonify({ "error": str(e) }), 500

# Save favourite
@app.route('/api/favourite', methods=['POST'])
def save_favourite():
    data = request.json
    user_id = data.get('user_id')
    tool_id = data.get('tool_id')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO favourites (user_id, tool_id) VALUES (?, ?)', (user_id, tool_id))
    conn.commit()
    conn.close()
    return jsonify({ "message": "Saved to favourites!" })

# Get favourites
@app.route('/api/favourites/<int:user_id>', methods=['GET'])
def get_favourites(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT tools.* FROM tools
        JOIN favourites ON tools.id = favourites.tool_id
        WHERE favourites.user_id = ?
    ''', (user_id,))
    tools = cursor.fetchall()
    conn.close()
    return jsonify([{
        'id': t[0], 'name': t[1], 'description': t[2],
        'category': t[3], 'link': t[4], 'emoji': t[5]
    } for t in tools])

# Ask AI
@app.route('/api/ask-ai', methods=['POST'])
def ask_ai():
    try:
        data = request.json
        user_message = data.get('message')
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{ "role": "user", "content": user_message }]
        )
        reply = response.choices[0].message.content
        return jsonify({ "reply": reply })
    except Exception as e:
        return jsonify({ "error": str(e) }), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))