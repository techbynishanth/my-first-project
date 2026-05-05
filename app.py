from flask import Flask, jsonify, request
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv
import sqlite3
import os

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

print("API KEY LOADED:", GROQ_API_KEY)  # we'll check if key loads

groq_client = Groq(api_key=GROQ_API_KEY)

# Create database
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Save user
@app.route('/api/save-user', methods=['POST'])
def save_user():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (name, email) VALUES (?, ?)', (name, email))
    conn.commit()
    conn.close()
    return jsonify({ "message": "User saved to database!" })

# Get all users
@app.route('/api/get-users', methods=['GET'])
def get_users():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return jsonify(users)

# Ask AI
@app.route('/api/ask-ai', methods=['POST'])
def ask_ai():
    try:
        data = request.json
        user_message = data.get('message')
        print("User asked:", user_message)

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{ "role": "user", "content": user_message }]
        )

        reply = response.choices[0].message.content
        print("AI replied:", reply)
        return jsonify({ "reply": reply })

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({ "error": str(e) }), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)