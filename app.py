import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Gerenciador de Uniformes", page_icon="👕", layout="centered")

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

# Centraliza logo e título


st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.image("img/logomercado.png", width=300)
st.markdown(
    """
    <h1>Gerenciador de Uniformes</h1>
    <p>Sistema para controle e gestão de uniformes</p>
    <p><i>Desenvolvido por Inacio Bovo</i></p>
    """,
    unsafe_allow_html=True
)
st.markdown("</div>", unsafe_allow_html=True)

# Menu de navegação
aba = st.sidebar.radio(
    "Menu",
    ("Cadastro de Funcionário", "Deletar Usuario","Consulta de Uniformes", "Relatório")
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
        usuario = st.selectbox("Selecione o usuário para deletar", df["Funcionário"])
        if st.button("Deletar"):
            df = df[df["Funcionário"] != usuario]
            df.to_csv(CSV_PATH, index=False)
            st.success(f"Usuário '{usuario}' deletado com sucesso!")
    


elif aba == "Consulta de Uniformes":
    st.subheader("Consulta de Uniformes")
    busca = st.text_input("Buscar por nome ou setor")
    df = carregar_cadastros()
    if busca:
        df = df[df["Funcionário"].str.contains(busca, case=False, na=False) | df["Setor"].str.contains(busca, case=False, na=False)]
    st.write("Tabela de uniformes cadastrados:")
    st.dataframe(df)

elif aba == "Relatório":
    st.subheader("Relatório de Uniformes")
    df = carregar_cadastros()
    st.write(f"Total de cadastros: {len(df)}")
    st.dataframe(df)