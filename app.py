import streamlit as st
import pandas as pd
import os
import datetime
import locale

# CONFIG: deve vir antes de chamadas st.* visíveis
st.set_page_config(page_title="Gerenciador de Uniformes", page_icon="img/icone.png", layout="centered")

# Tenta aplicar locale para pt_BR (melhora labels do datepicker)
try:
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
except Exception:
    # Não usamos st.warning antes do set_page_config; aqui é seguro
    st.warning("Não foi possível aplicar locale pt_BR.UTF-8 no sistema. As datas ainda funcionarão, mas alguns rótulos podem ficar em inglês.")

# Credenciais fixas
USUARIO = "admin"
SENHA = "admin123"

# --- Variáveis e Funções para controle de cadastros e estoque ---
CSV_PATH = "cadastro_funcionarios.csv"
ESTOQUE_ARQUIVO = "estoque.csv"
MODELOS_UNIFORME = ["Escolha", "Bota", "Camisa Azul", "Polo cinza", "Camisa Preta", "Blusa de frio", "Avental", "Calça Branca", "Camisa Branca", "Boné"]
TAMANHOS_UNIFORME = ["TAMANHO","PP", "P", "M", "G", "GG", "XG","NUMERAÇÃO","33","34","35","36","37","38","39","40","41","42","43","44","45","46","47"]


def carregar_cadastros():
    """Carrega o DataFrame de funcionários do arquivo CSV (garante colunas esperadas)."""
    cols = ["Funcionário", "Cpf", "Setor", "Empresa", "Tamanho", "Modelo", "Quantidade", "Data Entrega", "Observações"]
    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH, dtype=str)
            # garante que existam todas as colunas
            for c in cols:
                if c not in df.columns:
                    df[c] = ""
            return df[cols]
        except Exception:
            # se der problema lendo, retorna um DataFrame vazio com as colunas corretas
            return pd.DataFrame(columns=cols)
    else:
        return pd.DataFrame(columns=cols)

# Funções corrigidas para o estoque
def carregar_estoque():
    """Carrega o estoque do arquivo CSV, garantindo as colunas e que 'quantidade' seja int."""
    cols = ["modelo", "tamanho", "quantidade"]
    try:
        if os.path.exists(ESTOQUE_ARQUIVO):
            df = pd.read_csv(ESTOQUE_ARQUIVO, dtype=str)
            for c in cols:
                if c not in df.columns:
                    df[c] = "" if c != "quantidade" else 0
            # converte quantidade para inteiro
            df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").fillna(0).astype(int)
            return df[cols]
        else:
            df_estoque = pd.DataFrame(columns=cols)
            df_estoque.to_csv(ESTOQUE_ARQUIVO, index=False)
            return df_estoque
    except Exception as e:
        st.error(f"Erro ao carregar o estoque. Por favor, verifique o arquivo '{ESTOQUE_ARQUIVO}'. Erro: {e}")
        return pd.DataFrame(columns=cols)


def salvar_estoque(df):
    """Salva o DataFrame de estoque no arquivo CSV."""
    df.to_csv(ESTOQUE_ARQUIVO, index=False)


def salvar_cadastro(nome, cpf, setor, empresa, tamanho, modelo, quantidade, data_entrega, observacao):
    """Salva um novo cadastro de funcionário e dá baixa no estoque.

    OBS: agora aceita 'empresa' (corrige TypeError de parâmetros).
    """
    estoque_atual = carregar_estoque()

    # valida quantidade
    try:
        quantidade_int = int(quantidade)
        if quantidade_int <= 0:
            st.error("A quantidade deve ser maior que zero.")
            return False
    except Exception:
        st.error("A quantidade deve ser um número inteiro.")
        return False

    # formata data (se veio como date)
    if isinstance(data_entrega, (datetime.date, datetime.datetime)):
        data_str = data_entrega.strftime("%d/%m/%Y")
    else:
        data_str = str(data_entrega)

    # Verifica o estoque antes de cadastrar
    uniforme_em_estoque = estoque_atual[(estoque_atual["modelo"] == modelo) & (estoque_atual["tamanho"] == tamanho)]

    if uniforme_em_estoque.empty:
        st.error(f"Uniforme '{modelo}' no tamanho '{tamanho}' não encontrado no estoque.")
        return False

    estoque_disponivel = int(uniforme_em_estoque["quantidade"].iloc[0])
    if estoque_disponivel < quantidade_int:
        st.error(f"Estoque insuficiente. Disponível: {estoque_disponivel} unidade(s) de '{modelo}' tamanho '{tamanho}'.")
        return False
        
    # Dá baixa no estoque
    idx = uniforme_em_estoque.index[0]
    estoque_atual.loc[idx, "quantidade"] = estoque_disponivel - quantidade_int
    salvar_estoque(estoque_atual)

    # Salva o cadastro do funcionário
    df = carregar_cadastros()
    novo = pd.DataFrame([{
        "Funcionário": nome,
        "Cpf": cpf,
        "Setor": setor,
        "Empresa": empresa,
        "Tamanho": tamanho,
        "Modelo": modelo,
        "Quantidade": quantidade_int,
        "Data Entrega": data_str,
        "Observações": observacao
    }])
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(CSV_PATH, index=False)
    
    st.success(f"Cadastro de {nome} efetuado com sucesso!")
    st.success(f"Baixa de {quantidade_int} unidade(s) do uniforme '{modelo}' tamanho '{tamanho}' realizada no estoque.")
    return True


def editar_ou_salvar_cadastro(nome, cpf, setor, empresa, tamanho, modelo, quantidade, data_entrega, observacao):
    """
    Edita a quantidade de um uniforme existente para um funcionário ou
    adiciona um novo uniforme a ele. (assinatura alinhada com salvar_cadastro)
    """
    df = carregar_cadastros()
    try:
        quantidade_int = int(quantidade)
    except Exception:
        st.error("A quantidade deve ser um número inteiro.")
        return

    # formata data
    if isinstance(data_entrega, (datetime.date, datetime.datetime)):
        data_str = data_entrega.strftime("%d/%m/%Y")
    else:
        data_str = str(data_entrega)

    condicao = (df["Funcionário"] == nome) & (df["Tamanho"] == tamanho) & (df["Modelo"] == modelo)
    if condicao.any():
        index_linha = df[condicao].index[0]
        quantidade_atual = int(df.loc[index_linha, "Quantidade"])
        nova_quantidade = quantidade_atual + quantidade_int
        df.loc[index_linha, "Quantidade"] = nova_quantidade
        df.loc[index_linha, "Data Entrega"] = data_str
        st.success(f"Quantidade de uniformes de {nome} atualizada para {nova_quantidade}!")
    else:
        novo = pd.DataFrame([{
            "Funcionário": nome,
            "Cpf": cpf,
            "Setor": setor,
            "Empresa": empresa,
            "Tamanho": tamanho,
            "Modelo": modelo,
            "Quantidade": quantidade_int,
            "Data Entrega": data_str,
            "Observações": observacao
        }])
        df = pd.concat([df, novo], ignore_index=True)
        st.success(f"Novo uniforme adicionado com sucesso para {nome}!")

    df.to_csv(CSV_PATH, index=False)


# Inicializa o estado de sessão (evita AttributeError)
if "acesso_liberado" not in st.session_state:
    st.session_state["acesso_liberado"] = False

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
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos, tente novamente.")

# --- SISTEMA (após login) ---
if st.session_state["acesso_liberado"]:
    if st.sidebar.button("Sair"):
        st.session_state["acesso_liberado"] = False
        st.rerun()

    df = carregar_cadastros()

    st.image("img/logomercado.png", width=300)

    aba = st.sidebar.radio(
        "Menu",
        ("Cadastro de Funcionário", "Inátivar Usuario", "Consulta de Uniformes", "Relatório", "Editar Funcionário", "Estoque")
    )

    if aba == "Cadastro de Funcionário":
        st.subheader("Cadastro de Funcionário")
        nome = st.text_input("NOME DO FUNCIONÁRIO")
        cpf = st.text_input("CPF")
        setor = st.selectbox("SETOR", ["ADMINISTRATIVO", "OPERACIONAL", "LIMPEZA", "SEGURANÇA", "PREVENÇÃO DE PERDAS", "DEPÓSITO", "RESTAURANTE", "PADARIA", "FRIOS", "OPERADOR (A) DE CAIXA", "AÇOUGUE"])
        empresa = st.selectbox("Empresa",["Matriz", "Cecília", "Filial", "Agrobiga"])
        tamanho = st.selectbox("TAMANHO DO UNIFORME", TAMANHOS_UNIFORME)
        modelo = st.selectbox("MODELO" ,MODELOS_UNIFORME)
        quantidade = st.text_input("QUANTIDADE")
        data_entrega = st.date_input("DATA DE ENTREGA", value=datetime.date.today())
        observacao = st.text_area("OBSERVAÇÕES")

        if st.button("Salvar Cadastro"):
            if nome.strip() == "":
                st.error("O nome do funcionário é obrigatório.")
            elif modelo == "Escolha":
                st.error("Por favor, selecione um modelo de uniforme.")
            else:
                # chama com 9 parâmetros (assinatura atualizada)
                if salvar_cadastro(nome, cpf, setor, empresa, tamanho, modelo, quantidade, data_entrega, observacao):
                    st.rerun()

        st.markdown(
        """
        <p>Sistema de controle e gestão de uniformes</p>
        <p><i>Desenvolvido por Inacio Bovo</i></p>
        """,
        unsafe_allow_html=True
        )

    elif aba == "Inátivar Usuario":
        st.subheader("Inátivar Usuário")
        if df.empty:
            st.info("Nenhum usuário cadastrado.")
        else:
            busca = st.text_input("Buscar funcionário por nome ou Cpf para deletar")
            df_filtrado = df[
                df["Funcionário"].str.contains(busca, case=False, na=False) |
                df["Cpf"].astype(str).str.contains(busca, case=False, na=False)
            ]
            if not df_filtrado.empty:
                st.write("Resultados da busca:")
                st.dataframe(df_filtrado, hide_index=True)
                opcoes_deletar = df_filtrado["Funcionário"].tolist()
                usuario_para_deletar = st.selectbox("Selecione o funcionário para deletar", options=opcoes_deletar)
                if st.button("Deletar"):
                    df = df[df["Funcionário"] != usuario_para_deletar]
                    df.to_csv(CSV_PATH, index=False)
                    st.success(f"Usuário '{usuario_para_deletar}' inátivo com sucesso!")
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
        st.dataframe(df, hide_index=True)

    elif aba == "Relatório":
        st.subheader("Relatório de Uniformes")
        st.write(f"Total de cadastros: {len(df)}")
        st.dataframe(df, hide_index=True)
        
    elif aba == "Editar Funcionário":
        st.subheader("Editar Funcionário e Uniformes")
        if df.empty:
            st.info("Nenhum funcionário cadastrado para edição.")
        else:
            busca = st.text_input("Buscar funcionário por nome ou Cpf para editar")
            df_filtrado = df[
                df["Funcionário"].str.contains(busca, case=False, na=False) |
                df["Cpf"].astype(str).str.contains(busca, case=False, na=False)
            ]
            if not df_filtrado.empty:
                st.write("Resultados da busca:")
                st.dataframe(df_filtrado, hide_index=True)
                opcoes_editar = df_filtrado["Funcionário"].tolist()
                funcionario_selecionado = st.selectbox("Selecione o funcionário para editar", options=opcoes_editar)

                if funcionario_selecionado:
                    st.markdown(f"---")
                    st.subheader(f"Edição de Uniformes para {funcionario_selecionado}")
                    df_funcionario = df[df["Funcionário"] == funcionario_selecionado]
                    st.write("Uniformes Atuais:")
                    st.dataframe(df_funcionario, hide_index=True)

                    st.markdown("### Adicionar Novo Uniforme (ou Atualizar Existente)")
                    with st.form(key="form_adicionar_uniforme"):
                        cpf = df_funcionario.iloc[0]["Cpf"]
                        setor = df_funcionario.iloc[0]["Setor"]
                        empresa = df_funcionario.iloc[0].get("Empresa", "")
                        tamanho = st.selectbox("TAMANHO DO UNIFORME", TAMANHOS_UNIFORME)
                        modelo = st.selectbox("MODELO" ,MODELOS_UNIFORME)
                        quantidade = st.text_input("QUANTIDADE")
                        data_entrega = st.date_input("DATA DE ENTREGA", value=datetime.date.today())
                        observacao = st.text_area("OBSERVAÇÕES")
                        adicionar_btn = st.form_submit_button("Adicionar/Atualizar Uniforme")
                        

                        if adicionar_btn:
                            editar_ou_salvar_cadastro(funcionario_selecionado, cpf, setor, empresa, tamanho, modelo, quantidade, data_entrega, observacao)
                            st.rerun()

                    st.markdown("### Remover Uniforme(s)")
                    if not df_funcionario.empty:
                        df_para_remocao = df_funcionario.copy()
                        df_para_remocao["Uniforme Completo"] = df_para_remocao["Modelo"] + " | " + df_para_remocao["Tamanho"] + " | Qtd: " + df_para_remocao["Quantidade"].astype(str)
                        uniformes_selecionados = st.multiselect(
                            "Selecione o(s) uniforme(s) para remover ou diminuir a quantidade",
                            options=df_para_remocao["Uniforme Completo"].tolist()
                        )
                        quantidade_remover = st.number_input(
                            "Quantidade a remover (0 para remover a linha inteira)", 
                            min_value=0, 
                            value=0, 
                            step=1, 
                            format="%d"
                        )
                        if st.button("Remover/Diminuir Uniforme(s)"):
                            if uniformes_selecionados:
                                df_final = df.copy()
                                for u in uniformes_selecionados:
                                    index_linha = df_para_remocao[df_para_remocao["Uniforme Completo"] == u].index[0]
                                    if quantidade_remover > 0:
                                        quantidade_atual = int(df_final.loc[index_linha, "Quantidade"])
                                        nova_quantidade = quantidade_atual - quantidade_remover
                                        if nova_quantidade <= 0:
                                            df_final.drop(index_linha, inplace=True)
                                            st.success(f"Uniforme '{u}' removido completamente.")
                                        else:
                                            df_final.loc[index_linha, "Quantidade"] = nova_quantidade
                                            st.success(f"Quantidade do uniforme '{u}' atualizada para {nova_quantidade}.")
                                    else:
                                        df_final.drop(index_linha, inplace=True)
                                        st.success(f"Uniforme '{u}' removido completamente.")
                                df_final.to_csv(CSV_PATH, index=False)
                                st.rerun()
                            else:
                                st.warning("Por favor, selecione um ou mais uniformes para remover.")

            else:
                st.warning("Nenhum funcionário encontrado com o termo de busca.")

    elif aba == "Estoque":
        st.title("📦 Controle de Estoque")
        st.markdown("---")
        estoque_atual = carregar_estoque()

        with st.form(key='formulario_produto'):
            st.subheader("Adicionar/Atualizar Uniforme")
            uniforme = st.selectbox("Modelo de Uniforme", MODELOS_UNIFORME)
            tamanho = st.selectbox("Tamanho do Uniforme", TAMANHOS_UNIFORME)
            quantidade = st.number_input("Quantidade", min_value=0, step=1)
            botao_enviar = st.form_submit_button("Salvar alterações")
        
        if botao_enviar:
            if uniforme == "Escolha":
                st.error("Por favor, selecione um modelo de uniforme.")
            else:
                uniforme_em_estoque = estoque_atual[(estoque_atual["modelo"] == uniforme) & (estoque_atual["tamanho"] == tamanho)]
                
                if not uniforme_em_estoque.empty:
                    index = uniforme_em_estoque.index[0]
                    estoque_atual.loc[index, "quantidade"] += int(quantidade)
                    st.success(f"Estoque do uniforme '{uniforme}' tamanho '{tamanho}' atualizado para {estoque_atual.loc[index, 'quantidade']}.")
                else:
                    novo_uniforme = pd.DataFrame([{"modelo": uniforme, "tamanho": tamanho, "quantidade": int(quantidade)}])
                    estoque_atual = pd.concat([estoque_atual, novo_uniforme], ignore_index=True)
                    st.success(f"Uniforme '{uniforme}' tamanho '{tamanho}' adicionado ao estoque com {quantidade} unidades.")
                
                salvar_estoque(estoque_atual)
                st.rerun()

        st.markdown("---")
        st.subheader("Estoque Atual")
        estoque_atualizado = carregar_estoque()
        
        # Cria um selectbox para escolher o uniforme e o tamanho a ser removido
        estoque_disponivel_para_remocao = estoque_atualizado[estoque_atualizado['quantidade'] > 0].copy()
        if not estoque_disponivel_para_remocao.empty:
            estoque_disponivel_para_remocao['Uniforme e Tamanho'] = estoque_disponivel_para_remocao['modelo'] + ' | ' + estoque_disponivel_para_remocao['tamanho']
            uniforme_a_remover = st.selectbox("Selecione o uniforme para remover", options=['Selecione'] + estoque_disponivel_para_remocao['Uniforme e Tamanho'].tolist())
            
            if uniforme_a_remover != 'Selecione':
                quantidade_remover = st.number_input("Quantidade para remover", min_value=1, step=1)
                
                if st.button("Remover do Estoque"):
                    modelo_remover, tamanho_remover = uniforme_a_remover.split(' | ')
                    
                    uniforme_na_tabela = estoque_atualizado[(estoque_atualizado['modelo'] == modelo_remover) & (estoque_atualizado['tamanho'] == tamanho_remover)]
                    
                    if not uniforme_na_tabela.empty:
                        index = uniforme_na_tabela.index[0]
                        quantidade_atual = int(uniforme_na_tabela['quantidade'].iloc[0])
                        
                        if quantidade_remover >= quantidade_atual:
                            estoque_atualizado.drop(index, inplace=True)
                            st.success(f"Uniforme '{modelo_remover}' tamanho '{tamanho_remover}' removido completamente do estoque.")
                        else:
                            estoque_atualizado.loc[index, 'quantidade'] -= int(quantidade_remover)
                            st.success(f"Removido {quantidade_remover} unidade(s) do uniforme '{modelo_remover}' tamanho '{tamanho_remover}'.")
                        
                        salvar_estoque(estoque_atualizado)
                        st.rerun()
        
        st.markdown("---")
        st.subheader("Estoque Atualizado")
        st.dataframe(carregar_estoque(), hide_index=True)
