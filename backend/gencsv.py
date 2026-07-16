"""
Genera un CSV con i tickers disponibili nella libreria pytickersymbols,
insieme a nome azienda, paese, indici di appartenenza e industria/settore.

Installazione richiesta:
    pip install pytickersymbols

Uso:
    python genera_tickers_csv.py
    python genera_tickers_csv.py --output miei_ticker.csv
    python genera_tickers_csv.py --indici DAX FTSE_100 SP_500   # solo alcuni indici
"""

import argparse
import csv
import os
from pytickersymbols import PyTickerSymbols


def genera_csv_tickers(output_path: str = "C:/GIT/MyViewInvest/gen/tickers.csv", indici: list[str] | None = None) -> str:
    """
    Genera un CSV con i tickers e le relative industrie/settori.

    Args:
        output_path: percorso del file CSV da creare.
        indici: lista di indici da includere (es. ["DAX", "FTSE 100"]).
                 Se None, vengono usati TUTTI gli indici disponibili.

    Returns:
        Il percorso del file CSV creato.
    """
    stock_data = PyTickerSymbols()

    indici_disponibili = list(stock_data.get_all_indices())
    if indici is None:
        indici = indici_disponibili
    else:
        # validazione: segnala eventuali indici non trovati
        non_validi = [i for i in indici if i not in indici_disponibili]
        if non_validi:
            print(f"Attenzione: indici non riconosciuti e ignorati: {non_validi}")
        indici = [i for i in indici if i in indici_disponibili]

    # Usiamo il ticker (symbol) come chiave per evitare duplicati
    # (la stessa azienda può comparire in più indici, es. Adidas in DAX e EURO STOXX 50)
    righe: dict[str, dict] = {}

    for nome_indice in indici:
        try:
            stocks = stock_data.get_stocks_by_index(nome_indice)
        except Exception as e:
            print(f"Errore nel recupero dell'indice '{nome_indice}': {e}")
            continue

        for stock in stocks:
            symbol = stock.get("symbol") or ""
            if not symbol:
                continue

            nome = stock.get("name", "")
            paese = stock.get("country", "")
            industrie = stock.get("industries", []) or []
            industria_principale = industrie[0] if industrie else ""
            tutte_le_industrie = ", ".join(industrie)

            if symbol in righe:
                # aggiungiamo l'indice se l'azienda compare in più indici
                if nome_indice not in righe[symbol]["indici"]:
                    righe[symbol]["indici"].append(nome_indice)
            else:
                righe[symbol] = {
                    "ticker": symbol,
                    "nome": nome,
                    "paese": paese,
                    "industria_principale": industria_principale,
                    "tutte_le_industrie": tutte_le_industrie,
                    "indici": [nome_indice],
                }

    # crea la/le cartelle di destinazione se non esistono già
    cartella = os.path.dirname(output_path)
    if cartella:
        os.makedirs(cartella, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ticker", "nome", "paese", "industria_principale", "tutte_le_industrie", "indici"])
        for r in sorted(righe.values(), key=lambda x: x["ticker"]):
            writer.writerow([
                r["ticker"],
                r["nome"],
                r["paese"],
                r["industria_principale"],
                r["tutte_le_industrie"],
                "; ".join(r["indici"]),
            ])

    print(f"Creato '{output_path}' con {len(righe)} tickers unici (da {len(indici)} indici).")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera CSV di tickers con industria/settore")
    parser.add_argument("--output", default="C:/GIT/MyViewInvest/gen/tickers.csv", help="Nome del file CSV di output")
    parser.add_argument("--indici", nargs="*", default=None,
                         help="Elenco indici da includere (default: tutti). Es: DAX 'FTSE 100' SP_500")
    args = parser.parse_args()

    genera_csv_tickers(output_path=args.output, indici=args.indici)