import streamlit as st
import pandas as pd
import os
import datetime
import locale
import base64
import io # Necessário para lidar com arquivos em memória do Streamlit

# CONFIG: deve vir antes de chamadas st.* visíveis
st.set_page_config(page_title="Gerenciador de Uniformes", page_icon="img/icone.png", layout="centered")


# Credenciais fixas
USUARIO = "Rhsmmk"
SENHA = "]e<H3T@:/6f2"

# --- Variáveis e Funções para controle de cadastros e estoque ---
CSV_PATH = "cadastro_funcionarios.csv"
ESTOQUE_ARQUIVO = "estoque.csv"
PEDIDO_ARQUIVO = "pedidos_uniformes.csv" # Novo arquivo para solicitações

MODELOS_UNIFORME = ["Escolha", "Camiseta do Caixa", "Camisa Azul", "Polo cinza", "Camisa Preta", "Moletom azul (ziper)", "Moletom Branco", "Calça Branca", "Camisa Branca", "Moletom Azul", "Corta Vento Azul","Blazer"]
TAMANHOS_UNIFORME = ["TAMANHO","PP", "P", "M", "G", "GG", "G1","G2","G3","NUMERAÇÃO","33","34","35","36","37","38","39","40","41","42","43","44","45","46","47"]


# --- FUNÇÃO DE CONVERSÃO DE IMAGEM PARA BASE64 (INTEGRADA) ---
def convert_uploaded_file_to_base64(uploaded_file):
    """Converte um arquivo de upload do Streamlit (bytes) em uma string Base64 com prefixo MIME."""
    if uploaded_file is not None:
        try:
            # Lê o conteúdo do arquivo em memória (bytes)
            bytes_data = uploaded_file.read()
            # Codifica os bytes para Base64
            encoded_string = base64.b64encode(bytes_data).decode('utf-8')
            # Usa o MIME type do arquivo para o prefixo (data:image/...)
            mime_type = uploaded_file.type if uploaded_file.type else "image/png"
            return f"data:{mime_type};base64,{encoded_string}"
        except Exception as e:
            st.error(f"Erro ao processar a imagem: {e}")
            return None
    return None
# ---------------------------------------------------------------


def carregar_cadastros():
    """Carrega o DataFrame de funcionários do arquivo CSV (garante colunas esperadas)."""
    # ADICIONADA: Nova coluna 'Ficha_Base64' para armazenar a imagem da assinatura
    cols = ["Funcionário", "Cpf", "Setor", "Empresa", "Tamanho", "Modelo", "Quantidade", "Data Entrega", "Observações", "Ficha_Base64"]
    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH, dtype=str)
            # garante que existam todas as colunas
            for c in cols:
                if c not in df.columns:
                    df[c] = ""
            # Garante que 'Quantidade' seja tratada como número (para operações matemáticas)
            df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0).astype(int)
            return df[cols]
        except Exception:
            # se der problema lendo, retorna um DataFrame vazio com as colunas corretas
            return pd.DataFrame(columns=cols)
    else:
        return pd.DataFrame(columns=cols)

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


def carregar_solicitacoes():
    """Carrega o DataFrame de solicitações (pedidos) do arquivo CSV."""
    cols = ["Loja", "Modelo", "Tamanho", "Data_Solicitacao", "Quantidade", "Status"]
    if os.path.exists(PEDIDO_ARQUIVO):
        try:
            df = pd.read_csv(PEDIDO_ARQUIVO, dtype=str)
            for c in cols:
                if c not in df.columns:
                    df[c] = ""
            return df[cols]
        except Exception:
            return pd.DataFrame(columns=cols)
    else:
        df_pedidos = pd.DataFrame(columns=cols)
        df_pedidos.to_csv(PEDIDO_ARQUIVO, index=False)
        return df_pedidos

def salvar_solicitacao(loja, modelo, tamanho, quantidade):
    """Salva uma nova solicitação de uniforme no arquivo CSV de pedidos."""
    df_pedidos = carregar_solicitacoes()
    
    nova_solicitacao = pd.DataFrame([{
        "Loja": loja,
        "Modelo": modelo,
        "Tamanho": tamanho,
        "Data_Solicitacao": datetime.date.today().strftime("%d/%m/%Y"),
        "Quantidade": int(quantidade),
        "Status": "Pendente"
    }])
    
    df_pedidos = pd.concat([df_pedidos, nova_solicitacao], ignore_index=True)
    df_pedidos.to_csv(PEDIDO_ARQUIVO, index=False)
    
    return True

# ADICIONADO: Novo parâmetro ficha_base64
def salvar_cadastro(nome, cpf, setor, empresa, tamanho, modelo, quantidade, data_entrega, observacao, ficha_base64):
    """Salva um novo cadastro de funcionário, dá baixa no estoque e armazena a ficha Base64."""
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
        
    # --- LÓGICA DE DIMINUIÇÃO DE ESTOQUE (CADASTRO/ENTREGA) ---
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
        "Observações": observacao,
        "Ficha_Base64": ficha_base64 # AQUI: Salva a string Base64 da ficha
    }])
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(CSV_PATH, index=False)
    
    st.success(f"Cadastro de **{nome}** efetuado com sucesso!")
    st.success(f"Baixa de **{quantidade_int} unidade(s)** do uniforme **'{modelo}' tamanho '{tamanho}'** realizada no estoque.")
    if ficha_base64:
        st.success("Ficha de entrega assinada salva com sucesso!")
    return True

def aumentar_estoque(modelo, tamanho, quantidade_remover):
    """Adiciona a quantidade removida de volta ao estoque (DEVOLUÇÃO)."""
    df_estoque = carregar_estoque()
    
    condicao_estoque = (df_estoque["modelo"] == modelo) & (df_estoque["tamanho"] == tamanho)
    uniforme_em_estoque = df_estoque[condicao_estoque]

    if uniforme_em_estoque.empty:
        # Cria o registro de estoque se não existir
        novo_uniforme = pd.DataFrame([{"modelo": modelo, "tamanho": tamanho, "quantidade": quantidade_remover}])
        df_estoque = pd.concat([df_estoque, novo_uniforme], ignore_index=True)
        st.warning(f"Item '{modelo}' ({tamanho}) não encontrado no registro de estoque. Criado com **{quantidade_remover} unidade(s)** devolvida(s).")
    else:
        # Atualiza a quantidade
        idx_estoque = uniforme_em_estoque.index[0]
        quantidade_atual_estoque = int(uniforme_em_estoque["quantidade"].iloc[0])
        df_estoque.loc[idx_estoque, "quantidade"] = quantidade_atual_estoque + quantidade_remover
        st.success(f"Estoque do uniforme **'{modelo}' ({tamanho})** aumentado em **{quantidade_remover} unidade(s)** (Devolução).")

    salvar_estoque(df_estoque)
    return True


def remover_uniforme_do_funcionario(df_cadastro, index_linha_cadastro, modelo, tamanho, quantidade_remover):
    """
    Remove ou diminui a quantidade de uniforme de um funcionário
    E ADICIONA a quantidade removida de volta ao estoque.
    """
    if quantidade_remover <= 0:
        st.error("Quantidade a remover deve ser maior que zero.")
        return df_cadastro

    # 1. Aumentar o estoque (DEVOLUÇÃO)
    aumentar_estoque(modelo, tamanho, quantidade_remover)

    # 2. Diminuir/Remover do cadastro do funcionário
    quantidade_atual_cadastro = int(df_cadastro.loc[index_linha_cadastro, "Quantidade"])
    nova_quantidade_cadastro = quantidade_atual_cadastro - quantidade_remover
    
    if nova_quantidade_cadastro <= 0:
        # Remove a linha inteira do cadastro
        df_cadastro.drop(index_linha_cadastro, inplace=True)
        st.info(f"Registro de **'{modelo}' ({tamanho})** removido completamente do funcionário.")
    else:
        # Atualiza a quantidade no cadastro
        df_cadastro.loc[index_linha_cadastro, "Quantidade"] = nova_quantidade_cadastro
        st.info(f"Quantidade de **'{modelo}' ({tamanho})** do funcionário diminuída para **{nova_quantidade_cadastro}**.")
        
    # A Ficha Base64 desaparece com a linha se a quantidade final for <= 0 (drop)
    # Se a linha for atualizada, mantemos a ficha existente (se houver).
        
    return df_cadastro

def devolver_estoque_do_funcionario(df_cadastro, funcionario_nome):
    """
    Devolve todos os uniformes associados a um funcionário ao estoque.
    Esta função deve ser chamada antes de deletar o funcionário.
    """
    df_funcionario = df_cadastro[df_cadastro["Funcionário"] == funcionario_nome].copy()
    itens_devolvidos = 0
    
    if df_funcionario.empty:
        return 0 # Nada para devolver

    for index, row in df_funcionario.iterrows():
        modelo = row['Modelo']
        tamanho = row['Tamanho']
        quantidade = int(row['Quantidade'])
        
        # Chama a função existente para aumentar o estoque (devolução)
        # Nota: O aumentar_estoque já atualiza o arquivo de estoque.
        aumentar_estoque(modelo, tamanho, quantidade)
        itens_devolvidos += quantidade
        
    # Retorna o DataFrame de cadastro, mas a função de exclusão irá removê-los logo em seguida
    return itens_devolvidos
# ----------------------------------------------------


# Inicializa o estado de sessão (evita AttributeError)
if "acesso_liberado" not in st.session_state:
    st.session_state["acesso_liberado"] = False

# --- LOGIN ---
if not st.session_state["acesso_liberado"]:
    with st.form("form_login", clear_on_submit=False):
        # Assumindo que você tem um arquivo de imagem 'img/logomercado.png' no ambiente
        # Se não tiver, comente a linha abaixo para evitar erro.
        st.image("img/logomercado.png", width=300) 
        st.title("Gerenciador de Uniforme SMMK")
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

    # Assumindo que você tem um arquivo de imagem 'img/logomercado.png'
    # Se não tiver, comente a linha abaixo para evitar erro.
    

    aba = st.sidebar.radio(
        "Menu",
        ("Cadastro de Funcionário", "Inátivar Usuario", "Consulta de Uniformes", "Relatório", "Editar Funcionário", "Estoque", "Solicitação")
    )

    if aba == "Cadastro de Funcionário":
        st.subheader("Cadastro de Funcionário e Entrega de Uniforme")
        st.warning("Ao salvar o cadastro, a quantidade será **BAIXADA AUTOMATICAMENTE** do estoque.")
        
        with st.form("form_cadastro_uniforme", clear_on_submit=True):
            nome = st.text_input("NOME DO FUNCIONÁRIO")
            cpf = st.text_input("CPF")
            setor = st.selectbox("SETOR", ["ADMINISTRATIVO", "OPERACIONAL", "LIMPEZA", "SEGURANÇA", "PREVENÇÃO DE PERDAS", "DEPÓSITO", "RESTAURANTE", "PADARIA", "FRIOS", "OPERADOR (A) DE CAIXA", "AÇOUGUE"])
            empresa = st.selectbox("Empresa",["Matriz", "Cecília", "Filial", "Agrobiga"])
            tamanho = st.selectbox("TAMANHO DO UNIFORME", TAMANHOS_UNIFORME)
            modelo = st.selectbox("MODELO" ,MODELOS_UNIFORME)
            quantidade = st.text_input("QUANTIDADE")
            data_entrega = st.date_input("DATA DE ENTREGA", value=datetime.date.today())
            observacao = st.text_area("OBSERVAÇÕES")
            
            # NOVO CAMPO: Upload da Ficha Assinada
            st.markdown("### ✍️ Ficha de Entrega Assinada")
            ficha_assinada = st.file_uploader(
                "Faça o upload da imagem (JPEG/PNG) da ficha assinada.",
                type=['jpg', 'jpeg', 'png']
            )

            salvar_btn = st.form_submit_button("Salvar Cadastro")

            if salvar_btn:
                if nome.strip() == "":
                    st.error("O nome do funcionário é obrigatório.")
                elif modelo == "Escolha":
                    st.error("Por favor, selecione um modelo de uniforme.")
                elif tamanho == "TAMANHO" or tamanho == "NUMERAÇÃO":
                    st.error("Por favor, selecione o tamanho/numeração correta.")
                else:
                    # 1. Converte a imagem para Base64 antes de salvar
                    base64_ficha = convert_uploaded_file_to_base64(ficha_assinada) if ficha_assinada else ""
                    
                    # 2. Chama a função de salvar com o novo argumento (ficha_base64)
                    if salvar_cadastro(nome, cpf, setor, empresa, tamanho, modelo, quantidade, data_entrega, observacao, base64_ficha):
                        st.rerun()

        st.markdown(
        """
        <p>Sistema de controle e gestão de uniformes</p>
        <p><i>Desenvolvido por Inacio Bovo</i></p>
        """,
        unsafe_allow_html=True
        )

    elif aba == "Inátivar Usuario":
        st.subheader("Inátivar Usuário (Remove todos os registros)")
        st.error("ATENÇÃO: A inativação AGORA **DEVOLVE AUTOMATICAMENTE** todos os uniformes ao estoque antes de excluir o registro do funcionário.")
        
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
                # Pega nomes únicos para o selectbox
                opcoes_deletar = df_filtrado["Funcionário"].unique().tolist()
                usuario_para_deletar = st.selectbox("Selecione o funcionário para deletar", options=opcoes_deletar)
                
                if usuario_para_deletar:
                    # Filtra o histórico do funcionário selecionado
                    df_usuario_historico = df[df["Funcionário"] == usuario_para_deletar]
                    st.markdown("### Histórico de Uniformes do Funcionário")
                    st.dataframe(df_usuario_historico, hide_index=True)
                    
                    # Prepara o arquivo CSV para download
                    csv_relatorio = df_usuario_historico.to_csv(index=False).encode('utf-8')
                    nome_arquivo = f"Relatorio_Inativacao_{usuario_para_deletar.replace(' ', '_')}_{datetime.date.today()}.csv"

                    st.download_button(
                        label="⬇️ Salvar Relatório Individual (CSV)",
                        data=csv_relatorio,
                        file_name=nome_arquivo,
                        mime="text/csv",
                        key="download_report"
                    )
                    st.markdown("---")


                if st.button("Deletar e Devolver Estoque"):
                    
                    # --- Lógica CORRIGIDA: Devolver itens antes de deletar ---
                    itens_devolvidos = devolver_estoque_do_funcionario(df, usuario_para_deletar)
                    
                    # 1. Remove os registros do funcionário
                    df = df[df["Funcionário"] != usuario_para_deletar]
                    df.to_csv(CSV_PATH, index=False)
                    
                    # 2. Feedback
                    if itens_devolvidos > 0:
                        st.success(f"**SUCESSO:** {itens_devolvidos} item(ns) devolvido(s) ao estoque. Usuário '{usuario_para_deletar}' inátivo com sucesso!")
                    else:
                        st.success(f"Usuário '{usuario_para_deletar}' inátivo com sucesso! Nenhum uniforme para devolver.")
                        
                    st.rerun()
                
            else:
                st.warning("Nenhum funcionário encontrado com o termo de busca.")

    elif aba == "Consulta de Uniformes":
        st.subheader("Consulta de Uniformes por Funcionário")
        busca = st.text_input("Buscar por nome ou Cpf")
        
        df_consulta = df.copy()
        if busca:
            df_consulta = df_consulta[df_consulta["Funcionário"].str.contains(busca, case=False, na=False) |
                             df_consulta["Cpf"].astype(str).str.contains(busca, case=False, na=False)]
                             
        st.write("Tabela de uniformes cadastrados:")
        # Exclui a coluna Base64 para visualização na tabela principal
        df_para_tabela = df_consulta.drop(columns=["Ficha_Base64"], errors='ignore')
        st.dataframe(df_para_tabela, hide_index=True)

        st.markdown("---")
        st.subheader("Visualização de Fichas Assinadas (Base64)")
        
        # Filtra registros que possuem a string Base64 salva
        registros_com_ficha = df_consulta[df_consulta["Ficha_Base64"] != ""]
        
        if not registros_com_ficha.empty:
            # Cria uma lista de opções mais informativa para o SelectBox
            opcoes_ficha = registros_com_ficha["Funcionário"] + " | " + registros_com_ficha["Modelo"] + " | " + registros_com_ficha["Data Entrega"]
            
            ficha_selecionada = st.selectbox(
                "Selecione o registro para visualizar a Ficha Assinada:",
                options=["Selecione"] + opcoes_ficha.tolist(),
                key="select_ficha_assinada"
            )
            
            if ficha_selecionada != "Selecione":
                # Encontra o registro selecionado
                linha = registros_com_ficha[opcoes_ficha == ficha_selecionada].iloc[0]
                base64_data = linha["Ficha_Base64"]
                
                if base64_data:
                    # Streamlit renderiza a Base64 diretamente como imagem
                    # CORREÇÃO DE DEPRECIAÇÃO: use_container_width=True
                    st.image(base64_data, caption=f"Ficha de {linha['Funcionário']} - {linha['Modelo']} ({linha['Data Entrega']})", use_container_width=True)
                else:
                    st.info("Ficha não encontrada para este registro.")
        else:
            st.info("Nenhum registro possui uma ficha de entrega assinada salva em Base64.")

    elif aba == "Relatório":
        st.subheader("Relatório de Uniformes")
        st.write(f"Total de cadastros de uniformes: {len(df)}")
        # Exclui a coluna Base64 para visualização no relatório
        df_para_tabela = df.drop(columns=["Ficha_Base64"], errors='ignore')
        st.dataframe(df_para_tabela, hide_index=True)
        
    elif aba == "Editar Funcionário":
        st.subheader("Editar Funcionário e Uniformes (Devolução/Retirada Manual)")
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
                # Exibe a tabela apenas com as colunas relevantes para seleção
                st.dataframe(df_filtrado[["Funcionário", "Cpf", "Setor", "Empresa"]].drop_duplicates(), hide_index=True)
                
                opcoes_editar = df_filtrado["Funcionário"].unique().tolist()
                funcionario_selecionado = st.selectbox("Selecione o funcionário para editar", options=opcoes_editar)

                if funcionario_selecionado:
                    st.markdown(f"---")
                    st.subheader(f"Uniformes Atuais de **{funcionario_selecionado}**")
                    df_funcionario = df[df["Funcionário"] == funcionario_selecionado].copy()
                    st.dataframe(df_funcionario, hide_index=True)

                    # --- SEÇÃO 1: ADICIONAR UNIFORME ---
                    st.markdown("### ➕ Adicionar Uniforme (Retirada Manual)")
                    st.info("Esta ação **AUMENTA** a quantidade no cadastro do funcionário e **DÁ BAIXA** no estoque.")

                    with st.form("form_adicionar_uniforme_funcionario", clear_on_submit=True):
                        col1_add, col2_add = st.columns(2)
                        
                        with col1_add:
                            modelo_add = st.selectbox("MODELO para adicionar", MODELOS_UNIFORME, key="modelo_add")
                        with col2_add:
                            tamanho_add = st.selectbox("TAMANHO para adicionar", TAMANHOS_UNIFORME, key="tamanho_add")
                        
                        quantidade_add = st.number_input("QUANTIDADE a adicionar", min_value=1, value=1, step=1, format="%d", key="qtd_add")
                        data_entrega_add = st.date_input("NOVA DATA DE ENTREGA", value=datetime.date.today(), key="data_add")
                        observacao_add = st.text_area("OBSERVAÇÕES da adição", key="obs_add")
                        
                        adicionar_btn = st.form_submit_button(f"Adicionar Uniforme a {funcionario_selecionado}")

                        if adicionar_btn:
                            # 1. Validações
                            if modelo_add == "Escolha":
                                st.error("Por favor, selecione um modelo de uniforme.")
                            elif tamanho_add in ["TAMANHO", "NUMERAÇÃO"]:
                                st.error("Por favor, selecione o tamanho/numeração correta.")
                            elif quantidade_add <= 0:
                                st.error("A quantidade deve ser maior que zero.")
                            else:
                                # 2. Lógica de Checagem e Baixa no Estoque
                                estoque_atual = carregar_estoque()
                                
                                condicao_estoque = (estoque_atual["modelo"] == modelo_add) & (estoque_atual["tamanho"] == tamanho_add)
                                uniforme_em_estoque = estoque_atual[condicao_estoque]
                                
                                if uniforme_em_estoque.empty:
                                    st.error(f"Uniforme '{modelo_add}' no tamanho '{tamanho_add}' não encontrado no estoque.")
                                else:
                                    estoque_disponivel = int(uniforme_em_estoque["quantidade"].iloc[0])
                                    if estoque_disponivel < quantidade_add:
                                        st.error(f"Estoque insuficiente. Disponível: {estoque_disponivel} unidade(s) de '{modelo_add}' tamanho '{tamanho_add}'.")
                                    else:
                                        # 3. Dá baixa no estoque
                                        idx_estoque = uniforme_em_estoque.index[0]
                                        estoque_atual.loc[idx_estoque, "quantidade"] -= quantidade_add
                                        salvar_estoque(estoque_atual)
                                        
                                        # 4. Atualiza o cadastro do funcionário (df)
                                        
                                        # Encontra se o funcionário JÁ tem esse item cadastrado (mesmo nome, modelo e tamanho)
                                        condicao_cadastro = (df["Funcionário"] == funcionario_selecionado) & \
                                                            (df["Modelo"] == modelo_add) & \
                                                            (df["Tamanho"] == tamanho_add)
                                        
                                        if condicao_cadastro.any():
                                            # Se JÁ tem: Atualiza a quantidade
                                            index_linha = df[condicao_cadastro].index[0]
                                            quantidade_atual = int(df.loc[index_linha, "Quantidade"])
                                            nova_quantidade = quantidade_atual + quantidade_add
                                            
                                            df.loc[index_linha, "Quantidade"] = nova_quantidade
                                            df.loc[index_linha, "Data Entrega"] = data_entrega_add.strftime("%d/%m/%Y")
                                            df.loc[index_linha, "Observações"] = observacao_add
                                            
                                            st.success(f"**{quantidade_add}** unidade(s) adicionada(s) ao uniforme **'{modelo_add}' ({tamanho_add})**. Nova quantidade: **{nova_quantidade}**.")
                                            
                                        else:
                                            # Se NÃO tem: Adiciona uma nova linha
                                            novo = pd.DataFrame([{
                                                "Funcionário": funcionario_selecionado,
                                                "Cpf": df_funcionario["Cpf"].iloc[0] if not df_funcionario.empty else "",
                                                "Setor": df_funcionario["Setor"].iloc[0] if not df_funcionario.empty else "",
                                                "Empresa": df_funcionario["Empresa"].iloc[0] if not df_funcionario.empty else "",
                                                "Tamanho": tamanho_add,
                                                "Modelo": modelo_add,
                                                "Quantidade": quantidade_add,
                                                "Data Entrega": data_entrega_add.strftime("%d/%m/%Y"),
                                                "Observações": observacao_add,
                                                "Ficha_Base64": "" # Não há ficha de entrega Base64 neste fluxo de edição
                                            }])
                                            df = pd.concat([df, novo], ignore_index=True)
                                            st.success(f"Novo uniforme **'{modelo_add}' ({tamanho_add})** adicionado com **{quantidade_add} unidade(s)**.")

                                        # 5. Salva o DataFrame atualizado do cadastro
                                        df.to_csv(CSV_PATH, index=False)
                                        st.rerun()

                    st.markdown(f"---")

                    # --- SEÇÃO 2: REGISTRAR DEVOLUÇÃO ---
                    st.markdown("### ⚠️ Registrar Devolução (Aumenta o Estoque)")
                    st.info("Esta ação **DIMINUI** a quantidade no cadastro do funcionário e **AUMENTA** o estoque.")
                    
                    if not df_funcionario.empty:
                        # Cria uma coluna de identificação única para o multiselect
                        df_funcionario["Uniforme Completo"] = df_funcionario["Modelo"] + " | " + df_funcionario["Tamanho"].astype(str) + " | Qtd: " + df_funcionario["Quantidade"].astype(str)
                        
                        uniforme_a_devolver = st.selectbox(
                            "Selecione o uniforme que será devolvido",
                            options=['Selecione'] + df_funcionario["Uniforme Completo"].tolist()
                        )
                        
                        if uniforme_a_devolver != 'Selecione':
                            # Encontra a linha correspondente ao item selecionado
                            linha_selecionada = df_funcionario[df_funcionario["Uniforme Completo"] == uniforme_a_devolver].iloc[0]
                            
                            quantidade_max = int(linha_selecionada['Quantidade'])
                            quantidade_devolver = st.number_input(
                                f"Quantidade a ser devolvida (Máx: {quantidade_max})", 
                                min_value=1, 
                                max_value=quantidade_max,
                                value=1, 
                                step=1, 
                                format="%d",
                                key="qtd_devolver"
                            )
                            
                            if st.button("Registrar Devolução e Atualizar Estoque"):
                                if quantidade_devolver > 0 and quantidade_devolver <= quantidade_max:
                                    
                                    # Pega o index real da linha no DataFrame original (df)
                                    # Nota: O index deve ser o index do DataFrame principal (df), não do df_funcionario
                                    index_linha_original = df[
                                        (df["Funcionário"] == funcionario_selecionado) &
                                        (df["Modelo"] == linha_selecionada['Modelo']) &
                                        (df["Tamanho"] == linha_selecionada['Tamanho'])
                                    ].index[0]
                                    
                                    # Chama a função que gerencia a devolução e o estoque
                                    df = remover_uniforme_do_funcionario(
                                        df, 
                                        index_linha_original, 
                                        linha_selecionada['Modelo'], 
                                        linha_selecionada['Tamanho'], 
                                        quantidade_devolver
                                    )
                                    
                                    df.to_csv(CSV_PATH, index=False)
                                    st.rerun()
                                else:
                                    st.error("Quantidade de devolução inválida.")
                    else:
                        st.info("O funcionário não possui uniformes cadastrados.")


            else:
                st.warning("Nenhum funcionário encontrado com o termo de busca.")
    
    elif aba == "Solicitação":
        st.title("👕 Solicitação de Uniforme")
        st.markdown("Use esta aba para registrar pedidos de uniformes para lojas/setores.")
        
        OPCOES_LOJA = ["MATRIZ", "GRANADA", "AGROBIGA"]
        
        loja_solicitacao = st.selectbox("LOJA", OPCOES_LOJA)
        
        modelos_validos = [m for m in MODELOS_UNIFORME if m != "Escolha"]
        modelo_solicitacao = st.selectbox("Modelo", modelos_validos)
        
        tamanho_solicitacao = st.selectbox("Tamanho", TAMANHOS_UNIFORME)
        
        quantidade_solicitacao = st.number_input("Quantidade Solicitada", min_value=1, value=1, step=1, format="%d")

        if st.button("Registrar Solicitação"):
            if modelo_solicitacao and quantidade_solicitacao > 0:
                if salvar_solicitacao(loja_solicitacao, modelo_solicitacao, tamanho_solicitacao, quantidade_solicitacao):
                    st.rerun()
            else:
                st.error("Por favor, preencha todos os campos corretamente e defina uma quantidade maior que zero.")
                
        st.markdown("---")
        st.subheader("Solicitações Pendentes")
        df_pedidos = carregar_solicitacoes()
        
        if df_pedidos.empty:
            st.info("Nenhuma solicitação de uniforme registrada.")
        else:
            df_pendentes = df_pedidos[df_pedidos['Status'] == 'Pendente']
            st.dataframe(df_pendentes, hide_index=True)

    elif aba == "Estoque":
        st.title("📦 Controle de Estoque")
        st.markdown("---")
        estoque_atual = carregar_estoque()

        with st.form(key='formulario_produto_adicionar'):
            st.subheader("Adicionar/Atualizar Uniforme (Entrada Manual)")
            uniforme = st.selectbox("Modelo de Uniforme", MODELOS_UNIFORME)
            tamanho = st.selectbox("Tamanho do Uniforme", TAMANHOS_UNIFORME)
            quantidade = st.number_input("Quantidade a adicionar", min_value=0, step=1)
            botao_enviar = st.form_submit_button("Salvar Entrada de Uniformes")
        
        if botao_enviar:
            if uniforme == "Escolha":
                st.error("Por favor, selecione um modelo de uniforme.")
            elif tamanho in ["TAMANHO", "NUMERAÇÃO"]:
                st.error("Por favor, selecione o tamanho/numeração correta.")
            elif quantidade <= 0:
                 st.error("A quantidade a adicionar deve ser maior que zero.")
            else:
                uniforme_em_estoque = estoque_atual[(estoque_atual["modelo"] == uniforme) & (estoque_atual["tamanho"] == tamanho)]
                
                if not uniforme_em_estoque.empty:
                    index = uniforme_em_estoque.index[0]
                    # Adiciona a quantidade à existente
                    estoque_atual.loc[index, "quantidade"] += int(quantidade)
                    st.success(f"Estoque do uniforme '{uniforme}' tamanho '{tamanho}' atualizado para **{estoque_atual.loc[index, 'quantidade']}**.")
                else:
                    # Cria um novo registro
                    novo_uniforme = pd.DataFrame([{"modelo": uniforme, "tamanho": tamanho, "quantidade": int(quantidade)}])
                    estoque_atual = pd.concat([estoque_atual, novo_uniforme], ignore_index=True)
                    st.success(f"Uniforme '{uniforme}' tamanho '{tamanho}' adicionado ao estoque com **{quantidade} unidades**.")
                
                salvar_estoque(estoque_atual)
                st.rerun()

        st.markdown("---")
        st.subheader("Estoque Atual")
        # Exibe o estoque antes da remoção manual
        df_estoque_para_remover = carregar_estoque().copy()
        
        with st.form(key='formulario_produto_remover'):
            st.subheader("Remover Uniforme (Saída Manual)")
            estoque_disponivel_para_remocao = df_estoque_para_remover[df_estoque_para_remover['quantidade'] > 0].copy()
            
            opcoes_estoque = ['Selecione']
            if not estoque_disponivel_para_remocao.empty:
                estoque_disponivel_para_remocao['Uniforme e Tamanho'] = estoque_disponivel_para_remocao['modelo'] + ' | ' + estoque_disponivel_para_remocao['tamanho'] + ' (Qtd: ' + estoque_disponivel_para_remocao['quantidade'].astype(str) + ')'
                opcoes_estoque.extend(estoque_disponivel_para_remocao['Uniforme e Tamanho'].tolist())
                
            uniforme_a_remover_estoque = st.selectbox("Selecione o uniforme para dar baixa", options=opcoes_estoque)
            
            quantidade_remover_estoque = st.number_input("Quantidade para remover do estoque", min_value=1, step=1, key="remocao_estoque")
            
            botao_remover = st.form_submit_button("Remover do Estoque (Baixa Manual)")

            if botao_remover:
                if uniforme_a_remover_estoque != 'Selecione':
                    # Extrai modelo e tamanho
                    partes = uniforme_a_remover_estoque.split(' | ')
                    modelo_remover = partes[0].strip()
                    # Tenta obter a parte do tamanho e remove a informação da quantidade
                    tamanho_info = partes[1].strip()
                    if '(' in tamanho_info:
                        tamanho_remover = tamanho_info.split('(')[0].strip()
                    else:
                        tamanho_remover = tamanho_info.strip()
                    
                    uniforme_na_tabela = df_estoque_para_remover[(df_estoque_para_remocao['modelo'] == modelo_remover) & (df_estoque_para_remocao['tamanho'] == tamanho_remover)]
                    
                    if not uniforme_na_tabela.empty:
                        index = uniforme_na_tabela.index[0]
                        quantidade_atual = int(uniforme_na_tabela['quantidade'].iloc[0])
                        
                        if quantidade_remover_estoque > quantidade_atual:
                            st.error(f"Erro: A quantidade a remover ({quantidade_remover_estoque}) é maior que a disponível ({quantidade_atual}).")
                        else:
                            if quantidade_remover_estoque >= quantidade_atual:
                                df_estoque_para_remover.drop(index, inplace=True)
                                st.success(f"Uniforme '{modelo_remover}' tamanho '{tamanho_remover}' removido completamente do estoque.")
                            else:
                                df_estoque_para_remover.loc[index, 'quantidade'] -= int(quantidade_remover_estoque)
                                st.success(f"Removido **{quantidade_remover_estoque} unidade(s)** do uniforme '{modelo_remover}' tamanho '{tamanho_remover}'.")
                            
                            salvar_estoque(df_estoque_para_remover)
                            st.rerun()
                    else:
                        st.error("Item de estoque não encontrado. Por favor, selecione da lista.")
                else:
                    st.error("Por favor, selecione um item válido para remover.")

        st.markdown("---")
        st.subheader("Estoque Atualizado")
        st.dataframe(carregar_estoque(), hide_index=True)
