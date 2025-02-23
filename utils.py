from flask import Flask, request, jsonify, render_template
import sqlite3
import json
import requests

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE,
                        password TEXT
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS AIAssessments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        quiz_data TEXT,
                        score INTEGER
                    )''')
    
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/generate_quiz', methods=['POST'])
def generate_quiz():
    api_key = "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"  # Replaced with actual API key
    prompt = (
        "Generate a 20-question multiple-choice quiz for Computer Science students applying for a job. "
        "The quiz should include analytical, math, CS basics, and programming fundamentals questions. "
        "Provide the questions in a numbered list format."
    )
    try:
        response = requests.post(
            "https://api.groq.com/v1/generate",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={"prompt": prompt, "max_tokens": 500}
        )
        data = response.json()
        return jsonify({"quiz": data.get("choices", [{}])[0].get("text", "")})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)})

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    data = request.get_json()
    user_id = data.get('user_id')
    quiz_data = json.dumps(data.get('quiz_data'))
    score = data.get('score')

    if not user_id or not quiz_data:
        return jsonify({"error": "Invalid data"}), 400

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO AIAssessments (user_id, quiz_data, score) VALUES (?, ?, ?)", (user_id, quiz_data, score))
    conn.commit()
    conn.close()

    return jsonify({"message": "Quiz submitted successfully!"})

@app.route('/get_results/<user_id>', methods=['GET'])
def get_results(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT quiz_data, score FROM AIAssessments WHERE user_id = ?", (user_id,))
    results = cursor.fetchall()
    conn.close()
    
    return jsonify({"results": results})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
