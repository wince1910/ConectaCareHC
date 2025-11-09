import sys

sys.path.append('.')

# Importando todas as funções de CRUD baseadas no DB
# As importações de Paciente (C, U, D) e as de relacionamento já estavam
from ConectaCareHC.crud.operacoes import (
    # Funções de Paciente e Relacionamento
    cadastrar_paciente,
    atualizar_paciente_db,
    excluir_paciente_db,
    mostrar_pacientes,
    consultar_paciente_por_cpf,
    exportar_consulta_para_json,
    vincular_paciente,
    agendar_consulta,
    listar_consultas,
    # NOVAS IMPORTAÇÕES (Funções de Cuidador e Filtro)
    cadastrar_cuidador,  # C
    consultar_cuidador_por_cpf,  # R (Específico)
    mostrar_cuidadores,  # R (Todos)
    atualizar_cuidador_db,  # U
    excluir_cuidador_db,  # D
    filtrar_pacientes_por_idade  # R (Filtro)
)

from ConectaCareHC.utils.validacao import validar_entrada


# --- Submenus (Adaptação para refletir o DB) ---

def submenu_cadastro():
    # Menu para as operações de Create e Vínculo.
    while True:
        print("\n--- SUBMENU CADASTRO & VÍNCULO (DB) ---")
        print("1. Cadastrar Paciente (INSERT - com busca de CEP ViaCEP)")
        print("2. Cadastrar Cuidador(a) (INSERT - com busca de CEP ViaCEP)")  # Agora usa DB
        print("3. Vincular Paciente a Cuidador(a) (INSERT no VINCULOS)")  # Agora usa DB
        print("0. Voltar ao Menu Principal")

        opcao = validar_entrada("Escolha uma opção: ", "int")

        if opcao == 1:
            cadastrar_paciente()
        elif opcao == 2:
            cadastrar_cuidador()  # Função que insere no DB
        elif opcao == 3:
            vincular_paciente()  # Função que insere no DB
        elif opcao == 0:
            return
        else:
            print("Opção inválida. Escolha um número do menu.")


def submenu_consulta():
    # Menu para as operações de Agendamento, Leitura e Exportação.
    while True:
        print("\n--- SUBMENU CONSULTAS & EXPORTAÇÃO (DB) ---")
        # Leitura (R) do CRUD
        print("1. Consultar Paciente por CPF")
        print("2. Mostrar todos os Pacientes (SELECT * do DB)")
        print("3. Filtrar Pacientes por Idade Mínima (SELECT com WHERE no DB)")  # NOVO FILTRO
        print("4. Mostrar todos os Cuidadores(as) (SELECT * do DB)")  # NOVO CUIDADOR
        print("5. Consultar Cuidador por CPF")  # NOVO CUIDADOR
        print("---")
        print("6. Agendar Consulta (INSERT no AGENDAMENTOS)")
        print("7. Listar Consultas Agendadas de um Paciente (SELECT no AGENDAMENTOS)")
        print("8. Exportar Dados de Pacientes para JSON")  # R + JSON
        print("0. Voltar ao Menu Principal")

        opcao = validar_entrada("Escolha uma opção: ", "int")

        if opcao == 1:
            consultar_paciente_por_cpf()
        elif opcao == 2:
            mostrar_pacientes()
        elif opcao == 3:
            filtrar_pacientes_por_idade()  # R
        elif opcao == 4:
            mostrar_cuidadores()  # R
        elif opcao == 5:
            consultar_cuidador_por_cpf()  # R
        elif opcao == 6:
            agendar_consulta()
        elif opcao == 7:
            listar_consultas()
        elif opcao == 8:
            exportar_consulta_para_json()
        elif opcao == 0:
            return
        else:
            print("Opção inválida. Escolha um número do menu.")


def submenu_crud_manutencao():
    # Menu para as operações de Update e Delete (Manutenção de Dados).
    while True:
        print("\n--- MANUTENÇÃO CADASTRAL (UPDATE & DELETE no DB) ---")
        # Update (U) e Delete (D) do CRUD
        print("1. Atualizar Cadastro de Paciente (UPDATE no DB)")
        print("2. Atualizar Cadastro de Cuidador(a) (UPDATE no DB)")
        print("---")
        print("3. Excluir Cadastro de Paciente (DELETE no DB)")
        print("4. Excluir Cadastro de Cuidador(a) (DELETE no DB)")
        print("0. Voltar ao Menu Principal")

        opcao = validar_entrada("Escolha uma opção: ", "int")

        if opcao == 1:
            atualizar_paciente_db()
        elif opcao == 2:
            atualizar_cuidador_db()  # U - NOVO
        elif opcao == 3:
            excluir_paciente_db()
        elif opcao == 4:
            excluir_cuidador_db()  # D - NOVO
        elif opcao == 0:
            return
        else:
            print("Opção inválida. Escolha um número do menu.")


# --- Menu Principal ---

def menu_principal():
    # Menu principal do sistema.
    while True:
        print("\n======== SISTEMA DE GESTÃO - ORACLE/VIACEP ========")
        print("------------------- MENU PRINCIPAL -----------------------")
        print("1. Cadastro (INSERT & ViaCEP)")
        print("2. Consultas, Listagens e Exportação (SELECT & JSON)")
        print("3. Manutenção de Dados (UPDATE & DELETE)")
        print("4. Sair do Sistema")
        print("---------------------------------------------------------")

        try:
            opcao = validar_entrada("Escolha uma opção: ", "int")

            if opcao == 1:
                submenu_cadastro()
            elif opcao == 2:
                submenu_consulta()
            elif opcao == 3:
                submenu_crud_manutencao()
            elif opcao == 4:
                print("Encerrando o sistema. Até mais!")
                break
            else:
                print("\nOpção inválida! Escolha um número entre 1 e 4.")

        except Exception as e:
            print(f"\n Ocorreu um erro inesperado! Tente novamente. Detalhes: {e}")


if __name__ == "__main__":
    menu_principal()