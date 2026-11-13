import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Morelate - Check de Entrega", layout="centered")

st.title("🚛 Confirmação de Entrega - Morelate")
st.write("Preencha os dados abaixo para registrar o status da entrega.")

URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbxX9-wief5QWVZXADivEX8qVKkvraYaHES14qoyDE6Ey0REGX4IQR62l_tcnVSz0TTqwA/exec"
URL_LEITURA_CSV = "https://google.com"

numero_nf = st.text_input("📋 Número da Nota Fiscal:", placeholder="Ex: 105432")
motorista = st.selectbox("👤 Entregador:", ["Selecione...", "Carlos Silva", "Marcos Souza", "Roberto Lima"])
status = st.radio("📌 Status da Entrega:", ["🟢 Pedido Entregue OK", "🔴 Cancelado / Recusado"])

motivo_selecionado = "N/A"

if status == "🔴 Cancelado / Recusado":
    motivo_selecionado = st.selectbox(
        "⚠️ Motivo Real do Cancelamento:",
        [
            "Selecione...",
            "Dados da Fatura / Boleto Incorretos",
            "Emissão Indevida / Pedido Duplicado",
            "Desistência da Compra",
            "Avaria / Erro de Aplicação",
            "Cliente Ausente / Loja Fechada",
            "Recusa por Atraso"
        ]
    )

observacao = st.text_area("📝 Observações (opcional):", placeholder="Descreva brevemente o ocorrido...")

if st.button("🚀 Confirmar Registro", use_container_width=True):
    nf_limpa = numero_nf.strip()
    
    if not nf_limpa or not nf_limpa.isdigit():
        st.error("❌ Digite apenas números válidos para a Nota Fiscal.")
    elif motorista == "Selecione..." or (status == "🔴 Cancelado / Recusado" and motivo_selecionado == "Selecione..."):
        st.error("❌ Preencha o Entregador e o Motivo do cancelamento.")
    else:
        with st.spinner("Salvando entrega na planilha..."):
            fuso_br = ZoneInfo("America/Sao_Paulo")
            agora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")
            
            parametros = {
                "Data_Hora": agora,
                "Nota_Fiscal": nf_limpa,
                "Motorista": motorista,
                "Status": status,
                "Motivo_Real": motivo_selecionado,
                "Observacoes": observacao.strip()
            }
            
            try:
                resposta = requests.get(URL_APPS_SCRIPT, params=parametros, timeout=15)
                resultado = resposta.json()
                
                if resultado.get("status") == "duplicado":
                    st.warning(f"⚠️ Atenção: A Nota Fiscal {nf_limpa} já foi registrada anteriormente!")
                elif resultado.get("status") == "sucesso":
                    st.balloons()
                    st.success(f"✅ Nota Fiscal {nf_limpa} salva na planilha com sucesso às {agora}!")
                else:
                    st.error("❌ Não foi possível confirmar a gravação. Tente novamente.")
            except Exception as e:
                st.error(f"❌ Falha de conexão ao enviar os dados: {e}")

st.sidebar.header("🔒 Área da Logística")
senha = st.sidebar.text_input("Senha de acesso:", type="password")

if senha == "morelate2026":
    st.divider()
    st.subheader("📊 Últimos Registros na Planilha Google")
    try:
        df_existente = pd.read_csv(URL_LEITURA_CSV)
        st.dataframe(df_existente.tail(10), use_container_width=True)
    except Exception:
        st.info("Aguardando os primeiros registros.")
