from flask import Flask, request, jsonify, render_template_string
import requests
import json
import os

app = Flask(__name__)

TURNSTILE_SECRET_KEY = '0x4AAAAAABmbouUk7KGU1IAygOluOAu2ock' 


HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloudflare Turnstile Demo</title>
    <script src="https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onloadTurnstileCallback" defer></script>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 20px auto; text-align: center; display: none; }
        h1 { color: #333; margin-bottom: 20px; }
        #myWidget { margin: 20px 0; display: flex; justify-content: center; }
        .success-message { color: #28a745; font-weight: bold; margin-top: 15px; }
        .loading { color: #007bff; font-style: italic; }
        .error-message { color: #dc3545; font-weight: bold; margin-top: 15px; }
    </style>
</head>
<body>
    <div>
        <h1>Welcome</h1>
        <div id="myWidget"></div>
        <div id="status">Please complete the verification above</div>
    </div>
    
    <div class="container">
        <h2>🎉 Verification Complete!</h2>
        <p>You have successfully completed the Cloudflare Turnstile verification.</p>
        <div class="success-message">Access granted! Server validation successful.</div>
    </div>

    <script>
        window.onloadTurnstileCallback = function () {
            turnstile.render("#myWidget", {
                sitekey: "0x4AAAAAABmboj9Myyw7zLyd",
                callback: async function (token) {
                    console.log(`Challenge Success ${token}`);
                    
                    document.getElementById("status").innerHTML = "🔄 Verifying with server...";
                    document.getElementById("status").className = "loading";
                    
                    try {
                        const response = await fetch('/verify-turnstile', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ token: token })
                        });

                        const result = await response.json();
                        
                        if (response.ok && result.success) {
                            document.getElementById("status").innerHTML = "✅ Server verification successful!";
                            document.getElementById("status").style.color = "#28a745";
                            document.getElementById("status").className = "";
                            
                            setTimeout(() => {
                                document.querySelector(".container").style.display = "block";
                                document.getElementById("myWidget").style.display = "none";
                            }, 1500);
                        } else {
                            throw new Error(result.message || 'Server validation failed');
                        }
                    } catch (error) {
                        console.error('Server validation error:', error);
                        document.getElementById("status").innerHTML = "❌ Server verification failed. Please try again.";
                        document.getElementById("status").style.color = "#dc3545";
                        document.getElementById("status").className = "error-message";
                        turnstile.reset();
                    }
                },
                "error-callback": function(error) {
                    console.log("Turnstile error:", error);
                    document.getElementById("status").innerHTML = "❌ Verification failed. Please try again.";
                    document.getElementById("status").style.color = "#dc3545";
                }
            });
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/verify-turnstile', methods=['POST'])
def verify_turnstile():
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({
            'success': False,
            'message': 'No token provided'
        }), 400

    try:
        
        verify_data = {
            'secret': TURNSTILE_SECRET_KEY,
            'response': token,
        }
        
        
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
        if client_ip:
            verify_data['remoteip'] = client_ip

        verify_response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data=verify_data,  
            timeout=10
        )
        
        """
        verify_payload = {
            'secret': TURNSTILE_SECRET_KEY,
            'response': token,
        }
        if client_ip:
            verify_payload['remoteip'] = client_ip
            
        verify_response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            json=verify_payload,  # This sends as application/json
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        """
        
        verify_result = verify_response.json()
        
        print(f'Cloudflare verification result: {verify_result}')

        if verify_result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Token verified successfully',
                'challenge_ts': verify_result.get('challenge_ts'),
                'hostname': verify_result.get('hostname')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Token verification failed',
                'errors': verify_result.get('error-codes', [])
            }), 400

    except requests.RequestException as e:
        print(f'Error verifying Turnstile token: {e}')
        return jsonify({
            'success': False,
            'message': 'Internal server error during verification'
        }), 500

@app.route('/protected-content')
def protected_content():
    
    return jsonify({
        'message': 'This is protected content!',
        'data': 'Only verified users can see this'
    })

if __name__ == '__main__':
    app.run(debug=True, port=5500)
