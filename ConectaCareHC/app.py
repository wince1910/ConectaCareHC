# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
# Configura CORS para permitir todas as origens (ou especifique seu frontend)
CORS(app)

@app.route('/api/cep/<cep>', methods=['GET'])
def consultar_cep(cep):
    """Consulta o ViaCEP e retorna os dados do endereço"""
    try:
        # Remove qualquer formatação do CEP
        cep_limpo = cep.replace('-', '').replace('.', '').strip()
        
        if len(cep_limpo) != 8 or not cep_limpo.isdigit():
            return jsonify({'erro': 'CEP inválido'}), 400
        
        # Consulta o ViaCEP
        url = f'https://viacep.com.br/ws/{cep_limpo}/json/'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            
            if 'erro' in dados:
                return jsonify({'erro': 'CEP não encontrado'}), 404
            
            return jsonify({
                'cep': dados.get('cep', ''),
                'logradouro': dados.get('logradouro', ''),
                'complemento': dados.get('complemento', ''),
                'bairro': dados.get('bairro', ''),
                'localidade': dados.get('localidade', ''),
                'uf': dados.get('uf', '')
            })
        else:
            return jsonify({'erro': 'Erro ao consultar ViaCEP'}), 500
            
    except requests.exceptions.Timeout:
        return jsonify({'erro': 'Timeout ao consultar ViaCEP'}), 504
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)