def validar_entrada(texto, tipo="str"):
    """
    Função para validar entrada do usuário.

    Args:
        texto (str): O prompt a ser exibido ao usuário.
        tipo (str): O tipo de dado esperado ('str' ou 'int').

    Returns:
        A entrada validada (str ou int).
    """
    while True:
        try:
            entrada = input(texto).strip()

            if tipo == "int":
                # Tenta converter para int, garantindo que não há ponto decimal
                if not entrada.isdigit():
                    raise ValueError("O valor deve ser um número inteiro positivo.")

                valor_int = int(entrada)
                if valor_int < 0:
                    raise ValueError("O valor deve ser um número positivo.")
                return valor_int

            else:  # tipo == "str" (ou qualquer outro)
                if not entrada:  # Verifica se a string está vazia após o strip()
                    raise ValueError("A entrada não pode estar vazia.")
                return entrada

        except ValueError as e:
            # Tratamento de erro para inserção de dados
            print(f"**Entrada Inválida!** {e}")
            # Não é necessário 'finally' neste loop, pois o 'while' garante a repetição.