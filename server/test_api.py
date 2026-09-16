import requests

response = requests.post(
    "http://127.0.0.1:5000/api/generate-caption",
    json={
        "topic": "new coffee shop opening",
        "tone": "exciting",
        "platform": "Instagram"
    }
)

print(response.status_code)
print(response.json())