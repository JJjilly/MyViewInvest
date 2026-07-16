"""
screener.py — Logica principale dello stock screener
Scarica dati, calcola score, salva su Supabase.
Girata ogni notte da GitHub Actions.
"""

import os
import yfinance as yf
import pandas as pd
from datetime import datetime, date
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# ---------------------------------------------------------------------------
# Configurazione
# ---------------------------------------------------------------------------

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

def get_universe():
    df = pd.read_csv("gen/tickers.csv")
    return df["Ticker"].tolist()

tickers = get_universe()

# Universo di azioni da analizzare
# Modifica liberamente: aggiungi/rimuovi ticker


# ---------------------------------------------------------------------------
# Scoring — modifica i pesi e le soglie come vuoi
# ---------------------------------------------------------------------------

def calcola_score(row: dict) -> int:
    """
    Calcola uno score 0–100 basato su metriche fondamentali e tecniche.
    Modifica pesi e soglie in base alla tua strategia.
    """
    score = 0

    # --- Revenue Growth (0–25 punti) ---
    rg = row.get("revenue_growth")
    if rg is not None:
        if rg > 0.20:
            score += 25
        elif rg > 0.10:
            score += 15
        elif rg > 0.05:
            score += 8

    # --- Margine Netto (0–20 punti) ---
    mn = row.get("margine_netto")
    if mn is not None:
        if mn > 0.25:
            score += 20
        elif mn > 0.15:
            score += 12
        elif mn > 0.05:
            score += 5

    # --- Momentum 6 mesi (0–20 punti) ---
    m6 = row.get("momentum_6m")
    if m6 is not None:
        if m6 > 0.20:
            score += 20
        elif m6 > 0.10:
            score += 12
        elif m6 > 0:
            score += 6

    # --- P/E Ratio (0–15 punti) ---
    pe = row.get("pe_ratio")
    if pe is not None and pe > 0:
        if pe < 20:
            score += 15
        elif pe < 30:
            score += 10
        elif pe < 40:
            score += 5

    # --- Debt/Equity (0–10 punti) ---
    de = row.get("debt_equity")
    if de is not None:
        if de < 0.3:
            score += 10
        elif de < 0.7:
            score += 6
        elif de < 1.0:
            score += 2

    # --- Free Cash Flow positivo (0–10 punti) ---
    fcf = row.get("free_cash_flow")
    if fcf is not None and fcf > 0:
        score += 10

    return min(score, 100)


# ---------------------------------------------------------------------------
# Fetch dati da yfinance
# ---------------------------------------------------------------------------

def fetch_dati(ticker: str) -> dict | None:
    """Scarica e normalizza i dati di un ticker. Ritorna None se fallisce."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Prezzi storici per calcolo momentum
        prezzi = stock.history(period="1y")
        if prezzi.empty:
            return None

        close = prezzi["Close"]
        prezzo_attuale = float(close.iloc[-1])

        def momentum(giorni: int) -> float | None:
            if len(close) < giorni:
                return None
            return float((close.iloc[-1] - close.iloc[-giorni]) / close.iloc[-giorni])

        return {
            "ticker":           ticker,
            "nome":             info.get("longName"),
            "settore":          info.get("sector"),
            "pe_ratio":         info.get("trailingPE"),
            "revenue_growth":   info.get("revenueGrowth"),
            "margine_netto":    info.get("profitMargins"),
            "free_cash_flow":   info.get("freeCashflow"),
            "debt_equity":      info.get("debtToEquity"),
            "roe":              info.get("returnOnEquity"),
            "prezzo_attuale":   prezzo_attuale,
            "momentum_1m":      momentum(21),
            "momentum_3m":      momentum(63),
            "momentum_6m":      momentum(126),
            "momentum_1y":      momentum(252),
        }
    except Exception as e:
        print(f"  ⚠️  Errore su {ticker}: {e}")
        return None


# ---------------------------------------------------------------------------
# Filtro candidati — modifica le soglie minime che vuoi
# ---------------------------------------------------------------------------

def passa_filtro(row: dict) -> bool:
    """True se il titolo supera i criteri minimi per essere considerato."""
    return (
        (row.get("revenue_growth") or 0) > 0.05
        and (row.get("margine_netto") or 0) > 0.10
        and (row.get("momentum_6m") or -1) > 0
        and (row.get("score") or 0) >= 40
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"\n🍉 Screener avviato — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Universo: {len(tickers)} ticker\n")

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    oggi = date.today().isoformat()

    risultati = []

    for ticker in tickers:
        print(f"  → {ticker}", end=" ")
        dati = fetch_dati(ticker)
        if dati is None:
            print("❌")
            continue

        dati["score"] = calcola_score(dati)
        dati["passa_filtro"] = passa_filtro(dati)
        dati["aggiornato_il"] = datetime.now().isoformat()

        risultati.append(dati)
        print(f"✅  score={dati['score']}  filtro={dati['passa_filtro']}")

    if not risultati:
        print("\n❌ Nessun risultato — controlla connessione o ticker.")
        return

    # Salva risultati correnti (upsert = aggiorna se esiste)
    supabase.table("screener_results").upsert(risultati).execute()

    # Salva snapshot storico
    storico = [
        {
            "ticker":       r["ticker"],
            "score":        r["score"],
            "prezzo":       r["prezzo_attuale"],
            "data_run":     oggi,
            "passa_filtro": r["passa_filtro"],
        }
        for r in risultati
    ]
    supabase.table("screener_history").insert(storico).execute()

    candidati = [r for r in risultati if r["passa_filtro"]]
    print(f"\n✅ Completato: {len(risultati)} analizzati, {len(candidati)} candidati.\n")
    for c in sorted(candidati, key=lambda x: x["score"], reverse=True):
        print(f"   {c['ticker']:10} score={c['score']}  momentum6m={c.get('momentum_6m', 0):.1%}")


if __name__ == "__main__":
    main()
