import streamlit as st
import pandas as pd
import os

# CONFIG: deve vir antes de chamadas st.* visíveis
st.set_page_config(page_title="Gerenciador de Uniformes", page_icon="👕", layout="centered")

# Credenciais fixas
USUARIO = "admin"
SENHA = "admin123"

# Inicializa o estado de sessão (evita AttributeError)
if "acesso_liberado" not in st.session_state:
    st.session_state["acesso_liberado"] = False

# Título/boas-vindas
st.title("BEM-VINDO AO GERENCIADOR DE ATIVOS")

# --- LOGIN ---
if not st.session_state["acesso_liberado"]:
    with st.form("form_login", clear_on_submit=False):
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

    # Função para salvar cadastro
    def salvar_cadastro(nome, setor, tamanho, data_entrega, observacao):
        novo = pd.DataFrame([{
            "Funcionário": nome,
            "Setor": setor,
            "Tamanho": tamanho,
            "Data Entrega": str(data_entrega),
            "Observações": observacao
        }])
        if os.path.exists(CSV_PATH):
            df = pd.read_csv(CSV_PATH)
            df = pd.concat([df, novo], ignore_index=True)
        else:
            df = novo
        df.to_csv(CSV_PATH, index=False)

    # Função para carregar cadastros
    def carregar_cadastros():
        if os.path.exists(CSV_PATH):
            return pd.read_csv(CSV_PATH)
        else:
            return pd.DataFrame(columns=["Funcionário", "Setor", "Tamanho", "Data Entrega", "Observações"])

    # Cabeçalho com logo (verifique se o caminho existe)
    st.image("img/logomercado.png", width=300)
    st.markdown(
        """
        <h1>Gerenciador de Uniformes</h1>
        <p>Sistema para controle e gestão de uniformes</p>
        <p><i>Desenvolvido por Inacio Bovo</i></p>
        """,
        unsafe_allow_html=True
    )

    # Menu lateral
    aba = st.sidebar.radio(
        "Menu",
        ("Cadastro de Funcionário", "Deletar Usuario", "Consulta de Uniformes", "Relatório")
    )

    if aba == "Cadastro de Funcionário":
        st.subheader("Cadastro de Funcionário")
        nome = st.text_input("Nome do Funcionário")
        setor = st.selectbox("Setor", ["Administrativo", "Operacional", "Limpeza", "Segurança"])
        tamanho = st.selectbox("Tamanho do Uniforme", ["PP", "P", "M", "G", "GG", "XG"])
        data_entrega = st.date_input("Data de Entrega")
        observacao = st.text_area("Observações")

        if st.button("Salvar Cadastro"):
            if nome.strip() == "":
                st.error("O nome do funcionário é obrigatório.")
            else:
                salvar_cadastro(nome, setor, tamanho, data_entrega, observacao)
                st.success(f"Cadastro salvo para {nome}!")

    elif aba == "Deletar Usuario":
        st.subheader("Deletar Usuário")
        df = carregar_cadastros()
        if df.empty:
            st.info("Nenhum usuário cadastrado.")
        else:
            usuario_para_deletar = st.selectbox("Selecione o usuário para deletar", df["Funcionário"])
            if st.button("Deletar"):
                df = df[df["Funcionário"] != usuario_para_deletar]
                df.to_csv(CSV_PATH, index=False)
                st.success(f"Usuário '{usuario_para_deletar}' deletado com sucesso!")

    elif aba == "Consulta de Uniformes":
        st.subheader("Consulta de Uniformes")
        busca = st.text_input("Buscar por nome ou setor")
        df = carregar_cadastros()
        if busca:
            df = df[df["Funcionário"].str.contains(busca, case=False, na=False) |
                    df["Setor"].str.contains(busca, case=False, na=False)]
        st.write("Tabela de uniformes cadastrados:")
        st.dataframe(df)

    elif aba == "Relatório":
        st.subheader("Relatório de Uniformes")
        df = carregar_cadastros()
        st.write(f"Total de cadastros: {len(df)}")
        st.dataframe(df)
