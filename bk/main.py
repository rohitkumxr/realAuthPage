from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)
CLOUDFLARE_SECRET_KEY = os.environ.get("CLOUDFLARE_SECRET_KEY")

@app.route("/verify", methods=["POST"])
def verify():
    data = request.get_json()
    token = data.get("cf-turnstile-response")

    if not token:
        return jsonify({"success": False, "message": "Missing CAPTCHA token"}), 400

    verify_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    response = requests.post(
        verify_url,
        data={
            "secret": CLOUDFLARE_SECRET_KEY,
            "response": token
        }
    )

    result = response.json()
    return jsonify({"success": result.get("success", False), "message": result})


