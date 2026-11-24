
from datetime import datetime
from zoneinfo import ZoneInfo
import gspread
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Morelate - Torre de Controle", page_icon="📊", layout="wide"
)

# --- TRAVA DE SEGURANÇA PARA O GESTOR ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown(
            "<h2 style='text-align: center; color: #0B6E31;'>🔒 Torre de Controle Morelate</h2>",
            unsafe_allow_html=True,
        )
        st.info(
            "Acesso restrito à Gestão e Logística. Digite a senha para visualizar o painel ao vivo."
        )
        senha_digitada = st.text_input("Senha de acesso:", type="password")
        if st.button("Entrar no Painel", use_container_width=True):
            senha_correta = st.secrets.get("SENHA_GESTOR", "morelate2026")
            if senha_digitada == senha_correta:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta.")
    st.stop()

# --- ESTILO VISUAL EXECUTIVO ORIGINAL ---
st.markdown(
    """
    <style>
    .top-banner {
        background-color: #0B6E31;
        padding: 16px 24px;
        border-radius: 12px;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Conexão direta usando o ID da planilha
@st.cache_resource
def conectar_planilha():
    credenciais_dict = dict(st.secrets["connections"]["gsheets"])
    cliente = gspread.service_account_from_dict(credenciais_dict)
    planilha = cliente.open_by_key("1I3V8UxkeQyP1tO7TZIVbQk7HQrxv-FSsz5l3ChCMsV4")
    return planilha.sheet1


# Atualização automática a cada 30 segundos
@st.fragment(run_every=30)
def painel_ao_vivo():
    aba = conectar_planilha()
    dados = aba.get_all_records()
    df = pd.DataFrame(dados)

    fuso_br = ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")

    st.markdown(
        f"""
        <div class="top-banner">
            <div>
                <h2 style="margin:0; color:white;">🚛 Torre de Controle - Entregas Morelate</h2>
                <p style="margin:0; color:#D9F2E2;">Monitoramento em tempo real da operação</p>
            </div>
            <div style="text-align:right;">
                <span style="background:#085224; padding:8px 14px; border-radius:8px; font-weight:bold; color:white;">
                    🟢 AO VIVO • Atualizado às {agora}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.warning("Aguardando os primeiros registros na planilha...")
        return

    # Limpeza dos dados
    df["Nota_Fiscal"] = (
        df["Nota_Fiscal"]
        .fillna("")
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )
    df["Status"] = df["Status"].astype(str).str.strip()
    df["Motivo_Real"] = df["Motivo_Real"].fillna("N/A").astype(str).str.strip()
    df["Motorista"] = df["Motorista"].fillna("Não informado").astype(str).str.strip()
    df["Observações"] = df["Observações"].fillna("").astype(str).str.strip()

    # Filtro rápido de data
    hoje_str = datetime.now(fuso_br).strftime("%d/%m/%Y")
    col_filtro1, col_filtro2 = st.columns([1, 3])
    with col_filtro1:
        apenas_hoje = st.toggle("📅 Filtrar apenas entregas de HOJE", value=False)

    df_filtrado = (
        df[df["Data_Hora"].astype(str).str.startswith(hoje_str)]
        if apenas_hoje
        else df
    )

    # Indicadores principais (KPIs)
    total = len(df_filtrado)
    entregues = len(df_filtrado[df_filtrado["Status"].str.contains("Entregue")])
    recusados = len(df_filtrado[df_filtrado["Status"].str.contains("Cancelado")])
    taxa_sucesso = (entregues / total * 100) if total > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Total de Baixas", total)
    c2.metric("🟢 Entregues OK", entregues)
    c3.metric("🔴 Cancelados / Recusados", recusados)
    c4.metric("🎯 Taxa de Sucesso", f"{taxa_sucesso:.1f}%")

    st.divider()

    # Gráficos Lado a Lado
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("⚠️ Motivos de Cancelamento / Recusa")
        df_recusas = df_filtrado[df_filtrado["Status"].str.contains("Cancelado")]

        if not df_recusas.empty:
            contagem_motivos = (
                df_recusas["Motivo_Real"].value_counts().reset_index()
            )
            contagem_motivos.columns = ["Motivo", "Quantidade"]

            fig_motivos = px.bar(
                contagem_motivos,
                x="Quantidade",
                y="Motivo",
                orientation="h",
                text="Quantidade",
                color_discrete_sequence=["#D9381E"],
            )
            fig_motivos.update_layout(
                yaxis={"categoryorder": "total ascending"},
                xaxis_title="",
                yaxis_title="",
                height=360,
                margin=dict(l=0, r=20, t=10, b=0),
            )
            st.plotly_chart(fig_motivos, use_container_width=True)
        else:
            st.success("Nenhuma recusa registrada neste período!")

    with g2:
        st.subheader("🚛 Desempenho por Motorista / Placa")
        contagem_mot = (
            df_filtrado.groupby(["Motorista", "Status"])
            .size()
            .reset_index(name="Qtd")
        )

        fig_mot = px.bar(
            contagem_mot,
            x="Motorista",
            y="Qtd",
            color="Status",
            barmode="group",
            text="Qtd",
            color_discrete_map={
                "🟢 Pedido Entregue OK": "#0B6E31",
                "🔴 Cancelado / Recusado": "#D9381E",
            },
        )
        fig_mot.update_layout(
            xaxis_title="",
            yaxis_title="",
            legend_title="",
            height=360,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig_mot, use_container_width=True)

    # Tabela de últimas ocorrências críticas
    st.subheader("🚨 Últimas Notas Recusadas (Para Ação Imediata)")
    ultimas_recusas = df_filtrado[
        df_filtrado["Status"].str.contains("Cancelado")
    ].tail(10)
    if not ultimas_recusas.empty:
        st.dataframe(
            ultimas_recusas.iloc[::-1], use_container_width=True, hide_index=True
        )
    else:
        st.info("Nenhuma ocorrência de recusa registrada até o momento.")


painel_ao_vivo()
