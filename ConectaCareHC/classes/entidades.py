
# Incluindo a importação da nova função de utilidade para a API
import ConectaCareHC.utils.api_cep
from ConectaCareHC.utils.api_cep import buscar_endereco_por_cep

import json

class Paciente:
    #Representa um paciente no sistema.

    # O endereço será uma STRING formatada, mas internamente pode vir do CEP.
    def __init__(self, nome, cpf, idade, email, endereco, telefone_contato):
        self.nome = nome
        self.cpf = cpf
        self.idade = idade
        self.email = email
        self.endereco = endereco # Agora pode vir da API/CEP
        self.telefone_contato = telefone_contato
        self.agendamentos_paciente = [] # Manter para a lógica de consultas em memória/futura tabela
        # ... (Restante da classe Paciente permanece igual)

    def __str__(self):
        #Representação em string do objeto Paciente.
        return f"Nome: {self.nome}, CPF: {self.cpf}, Idade: {self.idade}, Endereço: {self.endereco}" # Incluído Endereço para mais detalhes

    def to_dict(self):
        #Retorna os atributos do paciente em formato de dicionário.
        return {
            'nome': self.nome,
            'cpf': self.cpf,
            'idade': self.idade,
            'email': self.email,
            'endereco': self.endereco,
            'telefone_contato': self.telefone_contato
        }

    def adicionar_consulta(self, data_consulta):
        #Adiciona uma data de consulta à lista de agendamentos.
        self.agendamentos_paciente.append({'data_consulta': data_consulta})

    def listar_consultas(self):
        #Lista as consultas agendadas para o paciente.
        if self.agendamentos_paciente:
            print(f"\nConsultas agendadas para {self.nome}:")
            for i, consulta in enumerate(self.agendamentos_paciente, start=1):
                print(f"{i}. Data: {consulta['data_consulta']}")
        else:
            print("\nNenhuma consulta encontrada para o paciente informado.")

# A classe Cuidador permanece a mesma
class Cuidador:
    #Representa um cuidador no sistema.

    def __init__(self, nome, cpf, idade, email, endereco, telefone_contato):
        self.nome = nome
        self.cpf = cpf
        self.idade = idade
        self.email = email
        self.endereco = endereco
        self.telefone_contato = telefone_contato
        self.pacientes_vinculados = []

    def __str__(self):
        #Representação em string do objeto Cuidador.
        return f"Nome: {self.nome}, CPF: {self.cpf}, Idade: {self.idade}"

    def to_dict(self):
        """Retorna os atributos do cuidador em formato de dicionário."""
        return {
            'nome': self.nome,
            'cpf': self.cpf,
            'idade': self.idade,
            'email': self.email,
            'endereco': self.endereco,
            'telefone_contato': self.telefone_contato
        }