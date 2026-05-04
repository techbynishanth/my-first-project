from flask import Flask, jsonify, request
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv
import sqlite3
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

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
    data = request.json
    user_message = data.get('message')

    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{ "role": "user", "content": user_message }]
    )

    reply = response.choices[0].message.content
    return jsonify({ "reply": reply })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)