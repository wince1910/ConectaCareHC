from flask import Flask, request, jsonify
import joblib


app = Flask(__name__) # Garanta que 'app' está definido globalmente

@app.route('/predict', methods=['POST'])


if __name__ == '__main__':
    # REMOVIDO: app.run(debug=True, host='0.0.0.0', port=5000)
    # O Gunicorn cuidará de rodar a API no Render
    print("API configurada para ser iniciada via Gunicorn.")