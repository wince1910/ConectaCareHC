# crud/operacoes.py (VERSÃO FINAL com DB, ViaCEP e Normalização)

import oracledb
import json
import os
from ConectaCareHC.classes.entidades import Paciente, Cuidador
from ConectaCareHC.crud.db_conexao import conectar_bd
from ConectaCareHC.utils.validacao import validar_entrada
from ConectaCareHC.utils.api_cep import buscar_endereco_por_cep


# --- Funções Auxiliares para DB ---

def executar_sql(sql, parametros=None, fetch_one=False, commit=False):
    """Função genérica para executar comandos SQL no Oracle."""
    conexao = conectar_bd()
    if not conexao:
        return None

    try:
        with conexao.cursor() as cursor:
            cursor.execute(sql, parametros or {})

            if commit:
                conexao.commit()
                return cursor.rowcount

            if fetch_one:
                return cursor.fetchone()

            return cursor.fetchall()

    except Exception as e:
        # Erro de integridade ORA-02292 ocorre ao tentar apagar uma chave primária referenciada
        if "ORA-02292" in str(e):
            print(
                f"Erro de Integridade: Não é possível excluir o registro. Existem dependências (vínculos ou agendamentos) em outras tabelas.")
        else:
            print(f"Erro na operação SQL: {e}")
        conexao.rollback()
        return None
    finally:
        pass


def inserir_endereco_db(dados_endereco):
    """Insere o endereço estruturado no DB e retorna o ID_ENDERECO (PRIMARY KEY)."""

    conexao = conectar_bd()
    if not conexao: return None

    sql = """
    INSERT INTO ENDERECOS 
        (CEP, LOGRADOURO, NUMERO, COMPLEMENTO, BAIRRO, CIDADE, UF) 
    VALUES 
        (:cep, :logradouro, :numero, :complemento, :bairro, :cidade, :uf) 
    RETURNING ID_ENDERECO INTO :id_endereco
    """

    try:
        with conexao.cursor() as cursor:
            # Cria uma variável bind para receber o ID
            id_retornado = cursor.var(oracledb.NUMBER)

            parametros = {
                'cep': dados_endereco.get('cep'),
                'logradouro': dados_endereco['logradouro'],
                'numero': dados_endereco['numero'],
                'complemento': dados_endereco['complemento'],
                'bairro': dados_endereco['bairro'],
                'cidade': dados_endereco['cidade'],
                'uf': dados_endereco['uf'],
                'id_endereco': id_retornado
            }

            cursor.execute(sql, parametros)
            conexao.commit()

            return id_retornado.getvalue()[0]

    except Exception as e:
        print(f" Erro ao inserir endereço no DB: {e}")
        conexao.rollback()
        return None


def formatar_endereco(row_a_partir_do_join):
    """Função auxiliar para formatar os dados de endereço vindos do JOIN."""
    # A ordem dos campos do JOIN no SELECT deve ser:
    # 5:Logradouro, 6:Numero, 7:Complemento, 8:Bairro, 9:Cidade, 10:UF, 11:CEP
    complemento = f" ({row_a_partir_do_join[7]})" if row_a_partir_do_join[7] else ""
    return (
        f"{row_a_partir_do_join[5]}, {row_a_partir_do_join[6]}{complemento} "
        f"- {row_a_partir_do_join[8]} ({row_a_partir_do_join[9]}/{row_a_partir_do_join[10]}) CEP: {row_a_partir_do_join[11]}"
    )


def coletar_dados_pessoa(tipo_pessoa):
    """Função auxiliar para coletar dados comuns e endereço estruturado (com prioridade para ViaCEP)."""
    print(f"\nCadastro de {tipo_pessoa}:")
    nome = validar_entrada("Nome: ")
    cpf = validar_entrada("CPF: ")
    idade = validar_entrada("Idade: ", "int")
    email = validar_entrada("Email: ")
    telefone_contato = validar_entrada("Telefone: ")

    dados_endereco = {}

    # Lógica de coleta de endereço estruturado (com ViaCEP)
    while True:
        cep = validar_entrada("Digite o CEP (apenas números, ou 0 para manual): ")

        if cep == '0':
            # Fallback completo para manual
            print("\nInsira o endereço manualmente.")
            dados_endereco = {
                'cep': None,
                'logradouro': validar_entrada("Logradouro: "),
                'numero': validar_entrada("Número: "),
                'complemento': input("Complemento (Opcional): ").strip() or None,
                'bairro': validar_entrada("Bairro: "),
                'cidade': validar_entrada("Cidade: "),
                'uf': validar_entrada("UF (Ex: SP): ")
            }
            break

        dados_cep = buscar_endereco_por_cep(cep)

        if dados_cep:
            # 1. Endereço encontrado via API (preenchimento automático)
            dados_endereco = {
                'cep': cep,
                'logradouro': dados_cep.get('logradouro', 'N/A'),
                'bairro': dados_cep.get('bairro', 'N/A'),
                'cidade': dados_cep.get('localidade', 'N/A'),
                'uf': dados_cep.get('uf', 'N/A'),
                'numero': validar_entrada("Número: "),
                'complemento': input("Complemento (Opcional): ").strip() or None
            }
            print(" Endereço base preenchido via ViaCEP.")
            break
        else:
            print(" Falha ao buscar CEP. Tente novamente ou digite 0 para inserir manualmente.")
            continue  # Volta para o topo do while

    return nome, cpf, idade, email, telefone_contato, dados_endereco


# --- Funções de Criação (Create) ---

def cadastrar_paciente():
    """Realiza o INSERT de Paciente e Endereço no DB Oracle."""
    nome, cpf, idade, email, telefone_contato, dados_endereco = coletar_dados_pessoa("Paciente")

    if not dados_endereco: return

    id_endereco = inserir_endereco_db(dados_endereco)

    if id_endereco is None: return

    sql = """
    INSERT INTO PACIENTES (NOME, CPF, IDADE, EMAIL, TELEFONE_CONTATO, ID_ENDERECO) 
    VALUES (:nome, :cpf, :idade, :email, :telefone_contato, :id_endereco)
    """
    parametros = {
        'nome': nome, 'cpf': cpf, 'idade': idade, 'email': email,
        'telefone_contato': telefone_contato, 'id_endereco': id_endereco
    }

    try:
        linhas_afetadas = executar_sql(sql, parametros, commit=True)
        if linhas_afetadas == 1:
            print(f"\n Paciente {nome} (CPF: {cpf}) cadastrado com sucesso no Oracle!")
        else:
            print("\n Nenhuma linha afetada. Cadastro de paciente falhou.")
    except Exception as e:
        print(f"\n Erro ao cadastrar paciente no DB: {e}")


def cadastrar_cuidador():
    """Realiza o INSERT de Cuidador e Endereço no DB Oracle."""
    nome, cpf, idade, email, telefone_contato, dados_endereco = coletar_dados_pessoa("Cuidador")

    if not dados_endereco: return

    id_endereco = inserir_endereco_db(dados_endereco)

    if id_endereco is None: return

    sql = """
    INSERT INTO CUIDADORES (NOME, CPF, IDADE, EMAIL, TELEFONE_CONTATO, ID_ENDERECO) 
    VALUES (:nome, :cpf, :idade, :email, :telefone_contato, :id_endereco)
    """
    parametros = {
        'nome': nome, 'cpf': cpf, 'idade': idade, 'email': email,
        'telefone_contato': telefone_contato, 'id_endereco': id_endereco
    }

    try:
        linhas_afetadas = executar_sql(sql, parametros, commit=True)
        if linhas_afetadas == 1:
            print(f"\n Cuidador {nome} (CPF: {cpf}) cadastrado com sucesso no Oracle!")
        else:
            print("\n Nenhuma linha afetada. Cadastro de cuidador falhou.")
    except Exception as e:
        print(f"\n Erro ao cadastrar cuidador no DB: {e}")


# --- Funções de Leitura (Read) ---

def listar_pacientes_db():
    """Realiza o SELECT de todos os Pacientes no DB Oracle (com JOIN)."""
    sql = """
    SELECT 
        P.NOME, P.CPF, P.IDADE, P.EMAIL, P.TELEFONE_CONTATO, P.ID_ENDERECO,
        E.LOGRADOURO, E.NUMERO, E.COMPLEMENTO, E.BAIRRO, E.CIDADE, E.UF, E.CEP
    FROM PACIENTES P
    JOIN ENDERECOS E ON P.ID_ENDERECO = E.ID_ENDERECO
    ORDER BY P.NOME
    """
    resultados = executar_sql(sql)

    if resultados is None or not resultados:
        print("\n  Nenhuma paciente cadastrado no banco de dados.")
        return []

    print("\n--- Todos os Pacientes Cadastrados no DB ---")

    for row in resultados:
        endereco_completo = formatar_endereco(row)
        paciente = Paciente(nome=row[0], cpf=row[1], idade=row[2], email=row[3],
                            endereco=endereco_completo, telefone_contato=row[4])
        print(f"  - {paciente}")

    return [row for row in resultados]  # Retorna os dados crus do DB


def consultar_paciente_por_cpf():
    """Consulta um paciente específico por CPF no DB (com JOIN)."""
    print("\n--- Consultar Paciente por CPF ---")
    cpf = validar_entrada("Digite o CPF do paciente a consultar: ")

    sql = """
    SELECT 
        P.NOME, P.CPF, P.IDADE, P.EMAIL, P.TELEFONE_CONTATO, P.ID_ENDERECO,
        E.LOGRADOURO, E.NUMERO, E.COMPLEMENTO, E.BAIRRO, E.CIDADE, E.UF, E.CEP
    FROM PACIENTES P
    JOIN ENDERECOS E ON P.ID_ENDERECO = E.ID_ENDERECO
    WHERE P.CPF = :cpf
    """
    parametros = {'cpf': cpf}

    resultado = executar_sql(sql, parametros, fetch_one=True)

    if resultado:
        endereco_completo = formatar_endereco(resultado)

        paciente = Paciente(nome=resultado[0], cpf=resultado[1], idade=resultado[2], email=resultado[3],
                            endereco=endereco_completo, telefone_contato=resultado[4])
        print("\n Paciente Encontrado:")
        print(f"Nome: {paciente.nome}, Idade: {paciente.idade}, Email: {paciente.email}, Endereço: {paciente.endereco}")
        return resultado  # Retorna o resultado completo do DB
    else:
        print(f"\n Paciente com CPF {cpf} não encontrado(a).")
        return None


def consultar_cuidador_por_cpf():
    """Consulta um cuidador específico por CPF no DB (com JOIN)."""
    print("\n--- Consultar Cuidador por CPF ---")
    cpf = validar_entrada("Digite o CPF do cuidador a consultar: ")

    sql = """
    SELECT 
        C.NOME, C.CPF, C.IDADE, C.EMAIL, C.TELEFONE_CONTATO, C.ID_ENDERECO,
        E.LOGRADOURO, E.NUMERO, E.COMPLEMENTO, E.BAIRRO, E.CIDADE, E.UF, E.CEP
    FROM CUIDADORES C
    JOIN ENDERECOS E ON C.ID_ENDERECO = E.ID_ENDERECO
    WHERE C.CPF = :cpf
    """
    parametros = {'cpf': cpf}

    resultado = executar_sql(sql, parametros, fetch_one=True)

    if resultado:
        endereco_completo = formatar_endereco(resultado)

        cuidador = Cuidador(nome=resultado[0], cpf=resultado[1], idade=resultado[2], email=resultado[3],
                            endereco=endereco_completo, telefone_contato=resultado[4])
        print("\n Cuidador Encontrado:")
        print(f"Nome: {cuidador.nome}, Idade: {cuidador.idade}, Email: {cuidador.email}, Endereço: {cuidador.endereco}")
        return resultado  # Retorna o resultado completo do DB
    else:
        print(f"\n Cuidador com CPF {cpf} não encontrado(a).")
        return None


def filtrar_pacientes_por_idade():
    """Filtra e lista pacientes por uma idade mínima a partir do DB (com JOIN)."""
    print("\n--- Filtrar Pacientes por Idade Mínima (DB) ---")

    try:
        idade_minima = validar_entrada("Digite a idade mínima para filtrar: ", "int")
    except Exception:
        print("Filtro cancelado.")
        return

    sql = """
    SELECT 
        P.NOME, P.CPF, P.IDADE, P.EMAIL, P.TELEFONE_CONTATO, P.ID_ENDERECO,
        E.LOGRADOURO, E.NUMERO, E.COMPLEMENTO, E.BAIRRO, E.CIDADE, E.UF, E.CEP
    FROM PACIENTES P
    JOIN ENDERECOS E ON P.ID_ENDERECO = E.ID_ENDERECO
    WHERE P.IDADE >= :idade_minima 
    ORDER BY P.IDADE DESC, P.NOME
    """
    parametros = {'idade_minima': idade_minima}

    pacientes_filtrados = executar_sql(sql, parametros)

    if pacientes_filtrados is None: return

    if pacientes_filtrados:
        print(f"\n--- Pacientes com {idade_minima} anos ou mais (DB) ---")
        for i, row in enumerate(pacientes_filtrados, start=1):
            endereco_completo = formatar_endereco(row)
            print(f"{i}. {row[0]} ({row[2]} anos) - End: {endereco_completo}")
    else:
        print(f"\nNenhum paciente encontrado com idade igual ou superior a {idade_minima} anos no DB.")


# --- Funções de Agendamento/Vínculo ---

def vincular_paciente():
    """Vincula um paciente a um cuidador no DB (Tabela VINCULOS_PACIENTE_CUIDADOR)."""
    print("\n--- Vínculo Paciente <-> Cuidador (DB) ---")

    cpf_paciente = validar_entrada("Digite o CPF do Paciente para vincular: ")
    paciente_info = executar_sql("SELECT NOME FROM PACIENTES WHERE CPF = :cpf", {'cpf': cpf_paciente}, fetch_one=True)
    if not paciente_info:
        print(f" Paciente com CPF {cpf_paciente} não encontrado(a) na base de dados.")
        return
    nome_paciente = paciente_info[0]

    cpf_cuidador = validar_entrada("Digite o CPF do Cuidador para vincular: ")
    cuidador_info = executar_sql("SELECT NOME FROM CUIDADORES WHERE CPF = :cpf", {'cpf': cpf_cuidador}, fetch_one=True)
    if not cuidador_info:
        print(f" Cuidador(a) com CPF {cpf_cuidador} não encontrado(a) na base de dados.")
        return
    nome_cuidador = cuidador_info[0]

    sql_check = "SELECT COUNT(*) FROM VINCULOS_PACIENTE_CUIDADOR WHERE CPF_PACIENTE = :cpf_paciente AND CPF_CUIDADOR = :cpf_cuidador"
    params_check = {'cpf_paciente': cpf_paciente, 'cpf_cuidador': cpf_cuidador}
    existe_vinculo = executar_sql(sql_check, params_check, fetch_one=True)[0]

    if existe_vinculo > 0:
        print(f"\n Paciente {nome_paciente} já está vinculado(a) ao(à) cuidador(a) {nome_cuidador}.")
        return

    sql_insert = "INSERT INTO VINCULOS_PACIENTE_CUIDADOR (CPF_PACIENTE, CPF_CUIDADOR) VALUES (:cpf_paciente, :cpf_cuidador)"
    try:
        linhas_afetadas = executar_sql(sql_insert, params_check, commit=True)
        if linhas_afetadas == 1:
            print(f"\n Vínculo criado: Paciente {nome_paciente} vinculado(a) ao(à) cuidador(a) {nome_cuidador}.")
        else:
            print("\n Nenhuma linha afetada. O vínculo pode não ter sido criado.")
    except Exception as e:
        print(f"\n Ocorreu um erro ao inserir o vínculo no DB: {e}")


def agendar_consulta():
    """Agenda uma nova consulta para um paciente no DB (Tabela AGENDAMENTOS)."""
    print("\n--- Agendamento de Consulta (DB) ---")

    cpf_paciente = validar_entrada("Digite o CPF do Paciente para agendar: ")
    paciente_info = executar_sql("SELECT NOME FROM PACIENTES WHERE CPF = :cpf", {'cpf': cpf_paciente}, fetch_one=True)
    if not paciente_info:
        print(f"Paciente com CPF {cpf_paciente} não encontrado(a) na base de dados.")
        return
    nome_paciente = paciente_info[0]

    data_consulta = validar_entrada("Digite a data da consulta (EX: DD/MM/AAAA): ")

    sql_insert = "INSERT INTO AGENDAMENTOS (CPF_PACIENTE, DATA_CONSULTA) VALUES (:cpf_paciente, TO_DATE(:data_consulta, 'DD/MM/YYYY'))"
    parametros = {'cpf_paciente': cpf_paciente, 'data_consulta': data_consulta}

    try:
        linhas_afetadas = executar_sql(sql_insert, parametros, commit=True)
        if linhas_afetadas == 1:
            print(f"\nConsulta marcada para {data_consulta} para o paciente {nome_paciente}.")
        else:
            print("\n Nenhuma linha afetada. O agendamento pode não ter sido concluído.")
    except Exception as e:
        print(f"\n Erro ao agendar consulta no DB: {e}")


def listar_consultas():
    """Lista as consultas agendadas de um paciente a partir do DB (Tabela AGENDAMENTOS)."""
    print("\n--- Listar Consultas Agendadas (DB) ---")

    cpf_paciente = validar_entrada("Digite o CPF do Paciente para listar as consultas: ")
    paciente_info = executar_sql("SELECT NOME FROM PACIENTES WHERE CPF = :cpf", {'cpf': cpf_paciente}, fetch_one=True)
    if not paciente_info:
        print(f" Paciente com CPF {cpf_paciente} não encontrado(a) na base de dados.")
        return
    nome_paciente = paciente_info[0]

    sql_select = "SELECT TO_CHAR(DATA_CONSULTA, 'DD/MM/YYYY') FROM AGENDAMENTOS WHERE CPF_PACIENTE = :cpf_paciente ORDER BY DATA_CONSULTA"
    parametros = {'cpf_paciente': cpf_paciente}

    agendamentos = executar_sql(sql_select, parametros)

    if agendamentos is None: return

    if agendamentos:
        print(f"\nConsultas agendadas para {nome_paciente}:")
        for i, (data_consulta_formatada,) in enumerate(agendamentos, start=1):
            print(f"{i}. Data: {data_consulta_formatada}")
    else:
        print(f"\nNenhuma consulta encontrada no DB para o paciente {nome_paciente}.")


# --- Funções de Atualização (Update) ---

def atualizar_paciente_db():
    """Realiza o UPDATE de Paciente e Endereço no DB Oracle."""
    print("\n--- Atualizar Cadastro de Paciente (DB) ---")

    cpf = validar_entrada("Digite o CPF do paciente que deseja atualizar: ")
    paciente_resultado = consultar_paciente_por_cpf()
    if not paciente_resultado: return

    # Extrai o ID_ENDERECO (índice 5 no SELECT com JOIN)
    id_endereco_atual = paciente_resultado[5]

    print("\nDeixe o campo em branco para manter o valor atual.")

    # 1. Coletar novos dados da PESSOA
    novo_nome = input(f"Novo Nome (atual: {paciente_resultado[0]}): ").strip() or paciente_resultado[0]
    nova_idade = paciente_resultado[2]
    nova_idade_str = input(f"Nova Idade (atual: {paciente_resultado[2]}): ").strip()
    if nova_idade_str:
        try:
            nova_idade = validar_entrada("Idade Válida: ", "int")
        except:
            print("Entrada Inválida! Idade não será alterada.")
    novo_email = input(f"Novo Email (atual: {paciente_resultado[3]}): ").strip() or paciente_resultado[3]
    novo_telefone = input(f"Novo Telefone (atual: {paciente_resultado[4]}): ").strip() or paciente_resultado[4]

    # 2. Coletar novos dados de ENDEREÇO (índices 6, 7, 8 no SELECT com JOIN)
    novo_logradouro = input(f"Novo Logradouro (atual: {paciente_resultado[6]}): ").strip() or paciente_resultado[6]
    novo_numero = input(f"Novo Número (atual: {paciente_resultado[7]}): ").strip() or paciente_resultado[7]
    novo_complemento = input(f"Novo Complemento (atual: {paciente_resultado[8]}): ").strip() or paciente_resultado[8]

    # 3. Executar UPDATES
    sql_paciente = "UPDATE PACIENTES SET NOME = :novo_nome, IDADE = :nova_idade, EMAIL = :novo_email, TELEFONE_CONTATO = :novo_telefone WHERE CPF = :cpf_original"
    params_paciente = {'novo_nome': novo_nome, 'nova_idade': nova_idade, 'novo_email': novo_email,
                       'novo_telefone': novo_telefone, 'cpf_original': cpf}

    sql_endereco = "UPDATE ENDERECOS SET LOGRADOURO = :log, NUMERO = :num, COMPLEMENTO = :comp WHERE ID_ENDERECO = :id_end"
    params_endereco = {'log': novo_logradouro, 'num': novo_numero, 'comp': novo_complemento,
                       'id_end': id_endereco_atual}

    try:
        # Commit True em ambas execuções
        linhas_paciente = executar_sql(sql_paciente, params_paciente, commit=True)
        linhas_endereco = executar_sql(sql_endereco, params_endereco, commit=True)

        if linhas_paciente >= 0 and linhas_endereco >= 0:
            print(f"\nCadastro de Paciente {cpf} atualizado com sucesso no Oracle!")
        else:
            print("\nOcorreu um erro ao atualizar um dos registros. Verifique a conexão.")
    except Exception as e:
        print(f"\n Erro ao atualizar paciente e endereço no DB: {e}")


def atualizar_cuidador_db():
    """Realiza o UPDATE de Cuidador e Endereço no DB Oracle."""
    print("\n--- Atualizar Cadastro de Cuidador (DB) ---")

    cpf = validar_entrada("Digite o CPF do cuidador que deseja atualizar: ")
    cuidador_resultado = consultar_cuidador_por_cpf()
    if not cuidador_resultado: return

    id_endereco_atual = cuidador_resultado[5]

    print("\nDeixe o campo em branco para manter o valor atual.")

    # 1. Coletar novos dados da PESSOA (Lógica similar ao paciente)
    novo_nome = input(f"Novo Nome (atual: {cuidador_resultado[0]}): ").strip() or cuidador_resultado[0]
    nova_idade = cuidador_resultado[2]
    nova_idade_str = input(f"Nova Idade (atual: {cuidador_resultado[2]}): ").strip()
    if nova_idade_str:
        try:
            nova_idade = validar_entrada("Idade Válida: ", "int")
        except:
            print("Entrada Inválida! Idade não será alterada.")
    novo_email = input(f"Novo Email (atual: {cuidador_resultado[3]}): ").strip() or cuidador_resultado[3]
    novo_telefone = input(f"Novo Telefone (atual: {cuidador_resultado[4]}): ").strip() or cuidador_resultado[4]

    # 2. Coletar novos dados de ENDEREÇO (Lógica similar ao paciente)
    novo_logradouro = input(f"Novo Logradouro (atual: {cuidador_resultado[6]}): ").strip() or cuidador_resultado[6]
    novo_numero = input(f"Novo Número (atual: {cuidador_resultado[7]}): ").strip() or cuidador_resultado[7]
    novo_complemento = input(f"Novo Complemento (atual: {cuidador_resultado[8]}): ").strip() or cuidador_resultado[8]

    # 3. Executar UPDATES
    sql_cuidador = "UPDATE CUIDADORES SET NOME = :novo_nome, IDADE = :nova_idade, EMAIL = :novo_email, TELEFONE_CONTATO = :novo_telefone WHERE CPF = :cpf_original"
    params_cuidador = {'novo_nome': novo_nome, 'nova_idade': nova_idade, 'novo_email': novo_email,
                       'novo_telefone': novo_telefone, 'cpf_original': cpf}

    sql_endereco = "UPDATE ENDERECOS SET LOGRADOURO = :log, NUMERO = :num, COMPLEMENTO = :comp WHERE ID_ENDERECO = :id_end"
    params_endereco = {'log': novo_logradouro, 'num': novo_numero, 'comp': novo_complemento,
                       'id_end': id_endereco_atual}

    try:
        linhas_cuidador = executar_sql(sql_cuidador, params_cuidador, commit=True)
        linhas_endereco = executar_sql(sql_endereco, params_endereco, commit=True)

        if linhas_cuidador >= 0 and linhas_endereco >= 0:
            print(f"\n Cadastro de Cuidador {cpf} atualizado com sucesso no Oracle!")
        else:
            print("\n Ocorreu um erro ao atualizar um dos registros. Verifique a conexão.")
    except Exception as e:
        print(f"\n Erro ao atualizar cuidador e endereço no DB: {e}")


# --- Funções de Exclusão (Delete) ---

def excluir_paciente_db():
    """Realiza o DELETE de Paciente e o DELETE em cascata do Endereço (se possível) no DB Oracle."""
    print("\n--- Excluir Cadastro de Paciente (DB) ---")

    cpf = validar_entrada("Digite o CPF do paciente que deseja EXCLUIR: ")
    paciente_info = executar_sql("SELECT ID_ENDERECO FROM PACIENTES WHERE CPF = :cpf", {'cpf': cpf}, fetch_one=True)
    if not paciente_info:
        print("\n Paciente com CPF não encontrado(a).")
        return

    id_endereco = paciente_info[0]

    confirmacao = validar_entrada(f"Tem certeza que deseja EXCLUIR o paciente com CPF {cpf}? (S/N): ").upper()

    if confirmacao == 'S':
        try:
            # 1. DELETE do Paciente (Obrigatório primeiro, devido à FK)
            linhas_paciente = executar_sql("DELETE FROM PACIENTES WHERE CPF = :cpf", {'cpf': cpf}, commit=True)

            # 2. Tentar DELETE do Endereço (Apenas se o paciente foi excluído)
            if linhas_paciente == 1:
                linhas_endereco = executar_sql("DELETE FROM ENDERECOS WHERE ID_ENDERECO = :id_end",
                                               {'id_end': id_endereco}, commit=True)
                print(f"\nPaciente e Endereço associado excluídos com sucesso do Oracle!")
            else:
                print("\n Paciente com CPF não encontrado(a).")
        except Exception:
            # A função executar_sql já trata o erro ORA-02292 (Foreign Key)
            pass
    else:
        print("Exclusão cancelada.")


def excluir_cuidador_db():
    """Realiza o DELETE de Cuidador e o DELETE em cascata do Endereço (se possível) no DB Oracle."""
    print("\n--- Excluir Cadastro de Cuidador (DB) ---")

    cpf = validar_entrada("Digite o CPF do cuidador que deseja EXCLUIR: ")
    cuidador_info = executar_sql("SELECT ID_ENDERECO FROM CUIDADORES WHERE CPF = :cpf", {'cpf': cpf}, fetch_one=True)
    if not cuidador_info:
        print("\n Cuidador com CPF não encontrado(a).")
        return

    id_endereco = cuidador_info[0]

    confirmacao = validar_entrada(f"Tem certeza que deseja EXCLUIR o cuidador com CPF {cpf}? (S/N): ").upper()

    if confirmacao == 'S':
        try:
            # 1. DELETE do Cuidador
            linhas_cuidador = executar_sql("DELETE FROM CUIDADORES WHERE CPF = :cpf", {'cpf': cpf}, commit=True)

            # 2. Tentar DELETE do Endereço
            if linhas_cuidador == 1:
                linhas_endereco = executar_sql("DELETE FROM ENDERECOS WHERE ID_ENDERECO = :id_end",
                                               {'id_end': id_endereco}, commit=True)
                print(f"\nCuidador e Endereço associado excluídos com sucesso do Oracle!")
            else:
                print("\n Cuidador com CPF não encontrado(a).")
        except Exception:
            # A função executar_sql já trata o erro ORA-02292 (Foreign Key)
            pass
    else:
        print("Exclusão cancelada.")


# --- Funções da Sprint 3 (Adaptadas para usar o DB) ---

def mostrar_pacientes():
    """Função de fachada para listar todos os pacientes do DB."""
    listar_pacientes_db()


def mostrar_cuidadores():
    """Realiza o SELECT de todos os Cuidadores no DB Oracle (com JOIN)."""
    sql = """
    SELECT 
        C.NOME, C.CPF, C.IDADE, C.EMAIL, C.TELEFONE_CONTATO, C.ID_ENDERECO,
        E.LOGRADOURO, E.NUMERO, E.COMPLEMENTO, E.BAIRRO, E.CIDADE, E.UF, E.CEP
    FROM CUIDADORES C
    JOIN ENDERECOS E ON C.ID_ENDERECO = E.ID_ENDERECO
    ORDER BY C.NOME
    """
    resultados = executar_sql(sql)

    if resultados is None or not resultados:
        print("\n ⚠️ Nenhuma cuidador cadastrado no banco de dados.")
        return []

    print("\n--- Todos os Cuidadores Cadastrados no DB ---")

    for row in resultados:
        endereco_completo = formatar_endereco(row)
        cuidador = Cuidador(nome=row[0], cpf=row[1], idade=row[2], email=row[3],
                            endereco=endereco_completo, telefone_contato=row[4])
        print(f"  - {cuidador}")

    return [row for row in resultados]  # Retorna os dados crus do DB


def exportar_consulta_para_json():
    """Realiza uma consulta e exporta o resultado para um arquivo JSON."""
    print("\n--- Exportar Dados de Pacientes (Consulta Completa) para JSON ---")

    sql = """
    SELECT 
        P.NOME, P.CPF, P.IDADE, P.EMAIL, P.TELEFONE_CONTATO,
        E.LOGRADOURO, E.NUMERO, E.COMPLEMENTO, E.BAIRRO, E.CIDADE, E.UF, E.CEP
    FROM PACIENTES P
    JOIN ENDERECOS E ON P.ID_ENDERECO = E.ID_ENDERECO
    ORDER BY P.NOME
    """
    resultados = executar_sql(sql)

    if resultados is None or not resultados:
        print("\n Não há dados para exportar ou ocorreu um erro de conexão.")
        return

    # Mapeamento para dicionários
    dados_para_json = []
    colunas = ['nome', 'cpf', 'idade', 'email', 'telefone_contato', 'logradouro', 'numero', 'complemento', 'bairro',
               'cidade', 'uf', 'cep']

    for row in resultados:
        dados_para_json.append(dict(zip(colunas, row)))

    nome_arquivo = "pacientes_consulta_exportada.json"

    try:
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados_para_json, f, ensure_ascii=False, indent=4)
        print(f"\n Sucesso! {len(dados_para_json)} registros exportados para '{nome_arquivo}'.")
    except IOError as e:
        print(f" Erro ao escrever o arquivo JSON: {e}")