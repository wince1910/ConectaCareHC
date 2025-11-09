import requests
import json


def buscar_endereco_por_cep(cep):
    """
    Busca o endereço completo usando a API pública ViaCEP.

    Args:
        cep (str): O CEP a ser consultado.

    Returns:
        dict: Um dicionário com os dados do endereço (logradouro, bairro, etc.) ou None em caso de erro.
    """
    # Remove caracteres não numéricos
    cep_limpo = ''.join(filter(str.isdigit, cep))

    if len(cep_limpo) != 8:
        print(" CEP inválido. Deve conter 8 dígitos.")
        return None

    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"

    try:
        # Consumo da API externa pública
        response = requests.get(url, timeout=5)  # Define um timeout de 5 segundos
        response.raise_for_status()  # Lança exceção para códigos de erro HTTP (4xx ou 5xx)

        dados = response.json()

        if dados.get('erro'):
            print(f" Erro ao buscar CEP {cep}: CEP não encontrado.")
            return None

        print(f" Endereço encontrado: {dados['logradouro']} - {dados['localidade']}/{dados['uf']}")
        return dados

    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar na ViaCEP ou timeout: {e}")
        return None
    except json.JSONDecodeError:
        print("Erro ao decodificar a resposta JSON da API.")
        return None