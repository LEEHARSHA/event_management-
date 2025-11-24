from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)
genai.configure(api_key="YOUR_API_KEY")

@app.route('/generate-plan', methods=['POST'])
def generate_plan():
    data = request.json
    model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
    # ... logic to call model ...
    return jsonify(response.text)

if __name__ == '__main__':
    app.run(debug=True)