from flask import Flask, jsonify, request, session
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "mysecretkey123"
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

# Create database
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

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
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[3], password):
        return jsonify({
            "message": "Login successful!",
            "user": { "id": user[0], "name": user[1], "email": user[2] }
        })
    else:
        return jsonify({ "error": "Invalid email or password!" }), 401

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
        print("ERROR:", str(e))
        return jsonify({ "error": str(e) }), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)