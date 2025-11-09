from flask import Flask, request, jsonify
import joblib

app = Flask(__name__) # Garanta que 'app' está definido globalmente

@app.route('/predict', methods=['POST'])
def predict():
    try:
        return jsonify({"message": "Endpoint de previsão acessado com sucesso! (Lógica interna a ser implementada)"})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':

    print("API configurada para ser iniciada via Gunicorn.")
