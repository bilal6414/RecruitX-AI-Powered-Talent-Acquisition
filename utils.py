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
import random

def rank_candidates(applications):
    """
    Dummy ranking function.
    In a real implementation, you would integrate your CV ranking algorithm
    (e.g. from your Jupyter Notebook code) here.
    For now, this function assigns a random score between 0 and 100 to each application.
    """
    ranked = []
    for app in applications:
        score = random.uniform(0, 100)  # Replace this with your real ranking logic
        ranked.append({
            'application_id': app.id,
            'candidate_id': app.candidate_id,
            'resume_path': app.resume_path,
            'score': score
        })
    # Sort candidates by score in descending order
    ranked.sort(key=lambda x: x['score'], reverse=True)
    return ranked
