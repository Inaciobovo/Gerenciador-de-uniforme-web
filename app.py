import streamlit as st
import pandas as pd
import os

# CONFIG: deve vir antes de chamadas st.* visíveis
st.set_page_config(page_title="Gerenciador de Uniformes", page_icon="img/icone.png", layout="centered")

# Credenciais fixas
USUARIO = "admin"
SENHA = "admin123"

# Inicializa o estado de sessão (evita AttributeError)
if "acesso_liberado" not in st.session_state:
    st.session_state["acesso_liberado"] = False

# Título/boas-vindas


# --- LOGIN ---
if not st.session_state["acesso_liberado"]:
    with st.form("form_login", clear_on_submit=False):
        st.image("img/logomercado.png", width=300)
        usuario_log = st.text_input("Usuário")
        senha_log = st.text_input("Senha", type="password")
        login_btn = st.form_submit_button("Login")

        if login_btn:
            if usuario_log == USUARIO and senha_log == SENHA:
                st.success("Login realizado com sucesso!")
                st.session_state["acesso_liberado"] = True
                # Opcional: forçar rerun para "limpar" a tela imediatamente
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos, tente novamente.")

# --- SISTEMA (após login) ---
if st.session_state["acesso_liberado"]:
    # Opção de sair (logout)
    if st.sidebar.button("Sair"):
        st.session_state["acesso_liberado"] = False
        st.rerun()

    CSV_PATH = "cadastro_funcionarios.csv"

    # Função para salvar cadastro (para novos funcionários)
    def salvar_cadastro(nome, cpf, setor, tamanho, modelo, quantidade, data_entrega, observacao):
        novo = pd.DataFrame([{
            "Funcionário": nome,
            "Cpf": cpf,
            "Setor": setor,
            "Tamanho": tamanho,
            "Modelo": modelo,
            "Quantidade": quantidade,
            "Data Entrega": str(data_entrega),
            "Observações": observacao
        }])
        if os.path.exists(CSV_PATH):
            df = pd.read_csv(CSV_PATH)
            df = pd.concat([df, novo], ignore_index=True)
        else:
            df = novo
        df.to_csv(CSV_PATH, index=False)

    # Função para editar ou adicionar um uniforme em um funcionário já existente
    def editar_ou_salvar_cadastro(nome, cpf, setor, tamanho, modelo, quantidade, data_entrega, observacao):
        # Carrega o DataFrame
        df = carregar_cadastros()
        
        # Converte a quantidade para inteiro para poder somar
        quantidade = int(quantidade)
        
        # Encontra a linha que corresponde ao funcionário, tamanho e modelo
        condicao = (df["Funcionário"] == nome) & (df["Tamanho"] == tamanho) & (df["Modelo"] == modelo)
        
        if condicao.any():
            # Se a linha existe, atualiza a quantidade
            index_linha = df[condicao].index[0]
            quantidade_atual = int(df.loc[index_linha, "Quantidade"])
            nova_quantidade = quantidade_atual + quantidade
            df.loc[index_linha, "Quantidade"] = nova_quantidade
            df.loc[index_linha, "Data Entrega"] = str(data_entrega) # Opcional: atualiza a data também
            st.success(f"Quantidade de uniformes de {nome} atualizada para {nova_quantidade}!")
        else:
            # Se não existe, cria uma nova linha
            novo = pd.DataFrame([{
                "Funcionário": nome,
                "Cpf": cpf,
                "Setor": setor,
                "Tamanho": tamanho,
                "Modelo": modelo,
                "Quantidade": quantidade,
                "Data Entrega": str(data_entrega),
                "Observações": observacao
            }])
            df = pd.concat([df, novo], ignore_index=True)
            st.success(f"Novo uniforme adicionado com sucesso para {nome}!")
            
        df.to_csv(CSV_PATH, index=False)


    # Função para carregar cadastros
    def carregar_cadastros():
        if os.path.exists(CSV_PATH):
            return pd.read_csv(CSV_PATH)
        else:
            return pd.DataFrame(columns=["Funcionário", "Cpf", "Setor", "Tamanho", "Modelo", "Quantidade", "Data Entrega", "Observações"])

    # Cabeçalho com logo (verifique se o caminho existe)
    st.image("img/logomercado.png", width=300)

    # Menu lateral
    aba = st.sidebar.radio(
        "Menu",
        ("Cadastro de Funcionário", "Deletar Usuario", "Consulta de Uniformes", "Relatório", "Editar Funcionário")
    )

    # NOVO CÓDIGO: Carrega o DataFrame de forma segura no início
    if os.path.exists(CSV_PATH):
        df = carregar_cadastros()
    else:
        df = pd.DataFrame(columns=["Funcionário", "Cpf", "Setor", "Tamanho", "Modelo", "Quantidade", "Data Entrega", "Observações"])


    if aba == "Cadastro de Funcionário":
        st.subheader("Cadastro de Funcionário")
        nome = st.text_input("NOME DO FUNCIONÁRIO")
        cpf = st.text_input("CPF")
        setor = st.selectbox("SETOR", ["ADMINISTRATIVO", "OPERACIONAL", "LIMPEZA", "SEGURANÇA", "PREVENÇÃO DE PERDAS", "DEPÓSITO", "RESTAURANTE", "PADARIA", "FRIOS", "OPERADOR (A) DE CAIXA", "AÇOUGUE"])
        tamanho = st.selectbox("TAMANHO DO UNIFORME", ["PP", "P", "M", "G", "GG", "XG"])
        modelo = st.selectbox("MODELO" ,["Escolha","Bota", "Camisa Azul", "Camisa cinza", "Camisa Preta", "Blusa de frio", "Avental", "Calça Branca", "Camisa Branca", "Boné"])
        quantidade = st.text_input("QUANTIDADE")
        data_entrega = st.date_input("DATA DE ENTREGA")
        observacao = st.text_area("OBSERVAÇÕES")

        if st.button("Salvar Cadastro"):
            if nome.strip() == "":
                st.error("O nome do funcionário é obrigatório.")
            else:
                salvar_cadastro(nome, cpf, setor, tamanho, modelo, quantidade, data_entrega, observacao)
                st.success(f"Cadastro de {nome} foi efetuado com sucesso!")

        st.markdown(
        """

        <p>Sistema de controle e gestão de uniformes</p>
        <p><i>Desenvolvido por Inacio Bovo</i></p>

        """,
        unsafe_allow_html=True
        )

    #deletar usuario (vai ser ultilizada quando algum funcionario for desligado da empresa)
    elif aba == "Deletar Usuario":
        st.subheader("Deletar Usuário")
        
        # A lógica de busca e deleção foi movida para dentro do `if/else`
        # para evitar erros quando o arquivo CSV não existe.
        if df.empty:
            st.info("Nenhum usuário cadastrado.")
        else:
            # Adiciona o campo de busca
            busca = st.text_input("Buscar funcionário por nome ou Cpf para deletar")
            
            # Filtra o DataFrame com base na busca
            df_filtrado = df[
                df["Funcionário"].str.contains(busca, case=False, na=False) |
                df["Cpf"].astype(str).str.contains(busca, case=False, na=False)
            ]

            if not df_filtrado.empty:
                # Exibe a tabela com os resultados da busca
                st.write("Resultados da busca:")
                st.dataframe(df_filtrado)

                # Use a lista filtrada para o selectbox
                opcoes_deletar = df_filtrado["Funcionário"].tolist()
                usuario_para_deletar = st.selectbox("Selecione o funcionário para deletar", options=opcoes_deletar)
                
                # Botão para deletar
                if st.button("Deletar"):
                    # Filtra o DataFrame original para remover o funcionário
                    df = df[df["Funcionário"] != usuario_para_deletar]
                    df.to_csv(CSV_PATH, index=False)
                    st.success(f"Usuário '{usuario_para_deletar}' deletado com sucesso!")
                    # Recarrega a página para atualizar a lista
                    st.rerun()

            else:
                st.warning("Nenhum funcionário encontrado com o termo de busca.")

    elif aba == "Consulta de Uniformes":
        st.subheader("Consulta de Uniformes")
        busca = st.text_input("Buscar por nome ou Cpf")
        if busca:
            df = df[df["Funcionário"].str.contains(busca, case=False, na=False) |
                     df["Cpf"].astype(str).str.contains(busca, case=False, na=False)]

        st.write("Tabela de uniformes cadastrados:")
        st.dataframe(df)

    elif aba == "Relatório":
        st.subheader("Relatório de Uniformes")
        st.write(f"Total de cadastros: {len(df)}")
        st.dataframe(df)
        
    # --- NOVA ABA: EDITAR FUNCIONÁRIO ---
    elif aba == "Editar Funcionário":
        st.subheader("Editar Funcionário e Uniformes")

        if df.empty:
            st.info("Nenhum funcionário cadastrado para edição.")
        else:
            # Campo de busca para o funcionário a ser editado
            busca = st.text_input("Buscar funcionário por nome ou Cpf para editar")
            df_filtrado = df[
                df["Funcionário"].str.contains(busca, case=False, na=False) |
                df["Cpf"].astype(str).str.contains(busca, case=False, na=False)
            ]

            # Se a busca encontrou resultados, exibe a tabela e permite a edição
            if not df_filtrado.empty:
                st.write("Resultados da busca:")
                st.dataframe(df_filtrado)

                # Use um selectbox para escolher o funcionário específico
                opcoes_editar = df_filtrado["Funcionário"].tolist()
                funcionario_selecionado = st.selectbox("Selecione o funcionário para editar", options=opcoes_editar)

                if funcionario_selecionado:
                    st.markdown(f"---")
                    st.subheader(f"Edição de Uniformes para {funcionario_selecionado}")

                    # Obter a 'pasta' do funcionário
                    df_funcionario = df[df["Funcionário"] == funcionario_selecionado]
                    
                    st.write("Uniformes Atuais:")
                    st.dataframe(df_funcionario)

                    # --- Adicionar uniforme ---
                    st.markdown("### Adicionar Novo Uniforme (ou Atualizar Existente)")
                    with st.form(key="form_adicionar_uniforme"):
                        cpf = df_funcionario.iloc[0]["Cpf"]
                        setor = df_funcionario.iloc[0]["Setor"]
                        
                        tamanho = st.selectbox("TAMANHO DO UNIFORME", ["PP", "P", "M", "G", "GG", "XG"])
                        modelo = st.selectbox("MODELO" ,["Escolha", "Bota", "Camisa Azul", "Camisa cinza", "Camisa Preta", "Blusa de frio", "Avental", "Calça Branca", "Camisa Branca", "Boné"])
                        quantidade = st.text_input("QUANTIDADE")
                        data_entrega = st.date_input("DATA DE ENTREGA")
                        observacao = st.text_area("OBSERVAÇÕES")

                        adicionar_btn = st.form_submit_button("Adicionar/Atualizar Uniforme")

                        if adicionar_btn:
                            # AQUI ESTÁ A MUDANÇA: chamamos a nova função
                            editar_ou_salvar_cadastro(funcionario_selecionado, cpf, setor, tamanho, modelo, quantidade, data_entrega, observacao)
                            st.rerun()

                    # --- Remover uniforme ---
                    st.markdown("### Remover Uniforme(s)")
                    if not df_funcionario.empty:
                        # Criar uma coluna combinada para facilitar a seleção
                        df_para_remocao = df_funcionario.copy()
                        df_para_remocao["Uniforme Completo"] = df_para_remocao["Modelo"] + " | " + df_para_remocao["Tamanho"] + " | Qtd: " + df_para_remocao["Quantidade"].astype(str)
                        
                        uniformes_selecionados = st.multiselect(
                            "Selecione o(s) uniforme(s) para remover ou diminuir a quantidade",
                            options=df_para_remocao["Uniforme Completo"].tolist()
                        )
                        
                        quantidade_remover = st.number_input(
                            "Quantidade a remover (deixar em branco para remover a linha inteira)", 
                            min_value=1, 
                            value=None, 
                            step=1, 
                            format="%d"
                        )
                        
                        if st.button("Remover/Diminuir Uniforme(s)"):
                            if uniformes_selecionados:
                                df_final = df.copy()
                                for u in uniformes_selecionados:
                                    # Encontra o índice da linha
                                    index_linha = df_para_remocao[df_para_remocao["Uniforme Completo"] == u].index[0]
                                    
                                    if quantidade_remover is not None and quantidade_remover > 0:
                                        # Diminui a quantidade
                                        quantidade_atual = int(df_final.loc[index_linha, "Quantidade"])
                                        nova_quantidade = quantidade_atual - quantidade_remover
                                        
                                        if nova_quantidade <= 0:
                                            # Se a quantidade for menor ou igual a zero, remove a linha
                                            df_final.drop(index_linha, inplace=True)
                                            st.success(f"Uniforme '{u}' removido completamente.")
                                        else:
                                            # Se a quantidade for maior que zero, apenas atualiza
                                            df_final.loc[index_linha, "Quantidade"] = nova_quantidade
                                            st.success(f"Quantidade do uniforme '{u}' atualizada para {nova_quantidade}.")
                                    else:
                                        # Se a quantidade não foi especificada, remove a linha inteira
                                        df_final.drop(index_linha, inplace=True)
                                        st.success(f"Uniforme '{u}' removido completamente.")
                                
                                # Salva o DataFrame atualizado
                                df_final.to_csv(CSV_PATH, index=False)
                                st.rerun()
                            else:
                                st.warning("Por favor, selecione um ou mais uniformes para remover.")

            else:
                st.warning("Nenhum funcionário encontrado com o termo de busca.")
