
import oracledb
import os
from dotenv import load_dotenv

load_dotenv()


class Credenciais:
    USER = os.getenv("ORACLE_USER", "rm565421")
    PASSWORD = os.getenv("ORACLE_PASSWORD", "090407")
    DSN = "oracle.fiap.com.br:1521/orcl"




def conectar_bd():
    """Tenta estabelecer uma conexão com o banco de dados Oracle."""
    try:
        # A conexão será fechada automaticamente ao sair do bloco 'with'
        conexao = oracledb.connect(user=Credenciais.USER, password=Credenciais.PASSWORD, dsn=Credenciais.DSN)
        print("Conexão com o banco de dados Oracle estabelecida!")
        return conexao
    except oracledb.Error as e:
        erro, = e.args
        print(f" Erro ao conectar ao Oracle: {erro.message}")
        print("Verifique suas credenciais e a disponibilidade do serviço.")
        return None

