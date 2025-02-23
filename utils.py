import requests

def generate_quiz():
    api_key = "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"
    prompt = (
        "Make a quiz for Computer Science students for hiring. "
        "The quiz consists of 20 MCQs including analytical, math, computer science basics, and programming fundamentals."
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
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}
