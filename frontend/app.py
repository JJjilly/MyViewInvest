"""
app.py — UI Web dello Stock Screener
Hostata su Streamlit Cloud, legge dati da Supabase.
"""

import os
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# ---------------------------------------------------------------------------
# Configurazione pagina
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Stock Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Connessione Supabase
# Streamlit Cloud legge i secrets da Settings → Secrets
# ---------------------------------------------------------------------------

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")
    if not url or not key:
        st.error("⚠️ Variabili SUPABASE_URL e SUPABASE_KEY non trovate.")
        st.stop()
    return create_client(url, key)


@st.cache_data(ttl=3600)  # cache 1 ora — i dati si aggiornano di notte
def carica_risultati() -> pd.DataFrame:
    supabase = get_supabase()
    res = supabase.table("screener_results").select("*").order("score", desc=True).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()


@st.cache_data(ttl=3600)
def carica_storico(ticker: str) -> pd.DataFrame:
    supabase = get_supabase()
    res = (
        supabase.table("screener_history")
        .select("data_run, score, prezzo")
        .eq("ticker", ticker)
        .order("data_run")
        .execute()
    )
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()


# ---------------------------------------------------------------------------
# Sidebar — filtri
# ---------------------------------------------------------------------------

st.sidebar.title("📈 Stock Screener")
st.sidebar.markdown("---")

mostra_solo_candidati = st.sidebar.toggle("Solo candidati", value=True)
score_min = st.sidebar.slider("Score minimo", 0, 100, 40)
settori = st.sidebar.multiselect(
    "Filtra per settore",
    options=["Technology", "Financial Services", "Healthcare",
             "Consumer Cyclical", "Industrials", "Energy", "Altro"],
    default=[],
)

st.sidebar.markdown("---")
st.sidebar.caption("Dati aggiornati ogni notte via GitHub Actions.")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

st.title("📈 Stock Screener")

df = carica_risultati()

if df.empty:
    st.warning("Nessun dato trovato. Assicurati di aver eseguito screener.py almeno una volta.")
    st.stop()

# Applica filtri
if mostra_solo_candidati:
    df = df[df["passa_filtro"] == True]

df = df[df["score"] >= score_min]

if settori:
    df = df[df["settore"].isin(settori)]

# Ultima data aggiornamento
if "aggiornato_il" in df.columns and not df.empty:
    ultima = df["aggiornato_il"].max()
    st.caption(f"Ultimo aggiornamento: {ultima[:16] if ultima else 'N/A'}")

# ---------------------------------------------------------------------------
# KPI header
# ---------------------------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)
col1.metric("Titoli analizzati", len(carica_risultati()))
col2.metric("Candidati", int(carica_risultati()["passa_filtro"].sum()) if not carica_risultati().empty else 0)
col3.metric("In visualizzazione", len(df))
col4.metric("Score medio", f"{df['score'].mean():.0f}" if not df.empty else "—")

st.markdown("---")

# ---------------------------------------------------------------------------
# Tabella risultati
# ---------------------------------------------------------------------------

if df.empty:
    st.info("Nessun titolo corrisponde ai filtri selezionati.")
else:
    colonne_display = [
        "ticker", "nome", "settore", "score",
        "prezzo_attuale", "pe_ratio",
        "revenue_growth", "margine_netto",
        "momentum_6m", "momentum_1y",
        "debt_equity"
    ]
    colonne_presenti = [c for c in colonne_display if c in df.columns]
    df_display = df[colonne_presenti].copy()

    # Formatta percentuali
    for col in ["revenue_growth", "margine_netto", "momentum_6m", "momentum_1y"]:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(
                lambda x: f"{x:.1%}" if pd.notna(x) else "—"
            )

    for col in ["prezzo_attuale", "pe_ratio", "debt_equity"]:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(
                lambda x: f"{x:.2f}" if pd.notna(x) else "—"
            )

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ticker":           st.column_config.TextColumn("Ticker"),
            "nome":             st.column_config.TextColumn("Azienda"),
            "settore":          st.column_config.TextColumn("Settore"),
            "score":            st.column_config.ProgressColumn("Score", min_value=0, max_value=100),
            "prezzo_attuale":   st.column_config.TextColumn("Prezzo $"),
            "pe_ratio":         st.column_config.TextColumn("P/E"),
            "revenue_growth":   st.column_config.TextColumn("Rev. Growth"),
            "margine_netto":    st.column_config.TextColumn("Margine"),
            "momentum_6m":      st.column_config.TextColumn("Mom. 6m"),
            "momentum_1y":      st.column_config.TextColumn("Mom. 1y"),
            "debt_equity":      st.column_config.TextColumn("D/E"),
        }
    )

# ---------------------------------------------------------------------------
# Dettaglio titolo
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("🔍 Dettaglio titolo")

ticker_list = df["ticker"].tolist() if not df.empty else []
if ticker_list:
    ticker_scelto = st.selectbox("Seleziona un titolo", ticker_list)

    storico = carica_storico(ticker_scelto)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f"**Score nel tempo — {ticker_scelto}**")
        if not storico.empty and "data_run" in storico.columns:
            st.line_chart(storico.set_index("data_run")["score"])
        else:
            st.info("Storico non ancora disponibile (serve almeno 2 run).")

    with col_b:
        st.markdown(f"**Prezzo nel tempo — {ticker_scelto}**")
        if not storico.empty and "prezzo" in storico.columns:
            st.line_chart(storico.set_index("data_run")["prezzo"])
        else:
            st.info("Storico non ancora disponibile.")
else:
    st.info("Seleziona filtri più ampi per vedere titoli.")
