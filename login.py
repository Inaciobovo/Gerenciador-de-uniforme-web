import streamlit as st

usuario= "admin"
senha = 'admin123'

st.text("BEM-VINDO AO GERENCIADOR DE ATIVOS")

usuario_log = st.text_input("Usuario")
senha_log = st.text_input("Senha")
login = st.button("Logins")

if usuario_log == usuario and senha_log == senha:
    msg = st.success("Login Realizado!") 
else:
    st.error("Usuario ou senha incorreto, tente novamente!")   