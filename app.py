

codigo_app = """import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Morelate - Check de Entrega", layout="centered")

st.title("🚛 Confirmação de Entrega - Morelate")
st.write("Preencha os dados abaixo para registrar o status da entrega.")

numero_nf = st.text_input("📋 Número da Nota Fiscal:", placeholder="Ex: 105432")

motorista = st.selectbox("👤 Entregador:", ["Selecione...", "Carlos Silva", "Marcos Souza", "Roberto Lima"])
status = st.radio("📌 Status da Entrega:", ["🟢 Pedido Entregue OK", "🔴 Cancelado / Recusado"])

motivo_selecionado = "N/A"
observacao = ""

if status == "🔴 Cancelado / Recusado":
    motivo_selecionado = st.selectbox(
        "⚠️ Motivo Real do Cancelamento:",
        ["Selecione...", "Cliente Ausente", "Recusa por Atraso", "Avaria na Mercadoria", "Erro de Preço/Boleto"]
    )
    observacao = st.text_area("📝 Observações (opcional):", placeholder="Descreva brevemente o ocorrido...")

arquivo_excel = "base_entregas_morelate.xlsx"

if st.button("🚀 Confirmar Registro", use_container_width=True):
    if not numero_nf.strip() or motorista == "Selecione..." or (status == "🔴 Cancelado / Recusado" and motivo_selecionado == "Selecione..."):
        st.error("❌ Preencha o número da Nota Fiscal, o Entregador e o Motivo (se cancelado).")
    else:
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        dados = {
            "Data_Hora": [agora],
            "Nota_Fiscal": [numero_nf.strip()],
            "Motorista": [motorista],
            "Status": [status],
            "Motivo_Real": [motivo_selecionado],
            "Observacoes": [observacao.strip()]
        }
        df_novo = pd.DataFrame(dados)
        
        try:
            if os.path.exists(arquivo_excel):
                df_final = pd.concat([pd.read_excel(arquivo_excel), df_novo], ignore_index=True)
            else:
                df_final = df_novo
                
            df_final.to_excel(arquivo_excel, index=False)
            st.balloons()
            st.success(f"✅ Nota Fiscal {numero_nf.strip()} salva com sucesso em {arquivo_excel}!")
        except PermissionError:
            st.error("⚠️ Erro de Permissão: O arquivo Excel está aberto! Por favor, feche a planilha e tente novamente.")

if os.path.exists(arquivo_excel):
    st.divider()
    with open(arquivo_excel, "rb") as f:
        st.download_button(
            label="📥 Baixar Planilha Atualizada (base_entregas_morelate.xlsx)",
            data=f,
            file_name="base_entregas_morelate.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
"""

with open("app.py", "w", encoding="utf-8") as f:
    f.write(codigo_app)

print("✅ Arquivo app.py atualizado com sucesso na sua pasta!")
