# 📈 Stock Screener

Sistema di screening azionario algoritmico con UI web e supporto futuro per app mobile.

## Architettura

```
stock-screener/
├── backend/          # Logica algoritmo Python (gira su GitHub Actions)
├── frontend/         # App web Streamlit (hostata su Streamlit Cloud)
├── mobile/           # App React Native futura (WatermelonDB locale + sync Supabase)
└── .github/
    └── workflows/    # Job notturno automatico
```

## Stack

| Componente        | Tecnologia         | Hosting            | Costo  |
|-------------------|--------------------|--------------------|--------|
| Database          | Supabase           | Supabase Cloud     | Free   |
| Logica algoritmo  | Python             | GitHub Actions     | Free   |
| UI Web            | Streamlit          | Streamlit Cloud    | Free   |
| App Mobile (futura)| React Native      | App Store / Play   | -      |
| Backup / versioning| GitHub            | GitHub             | Free   |

## Setup rapido

### 1. Clona il repo
```bash
git clone https://github.com/TUO_USERNAME/stock-screener.git
cd stock-screener
```

### 2. Installa dipendenze backend
```bash
cd backend
pip install -r requirements.txt
```

### 3. Configura variabili d'ambiente
Copia `.env.example` in `.env` e compila:
```bash
cp backend/.env.example backend/.env
```

### 4. Crea le tabelle su Supabase
Esegui il file `backend/db/schema.sql` nel SQL editor di Supabase.

### 5. Testa lo screener localmente
```bash
cd backend
python screener.py
```

### 6. Avvia la UI in locale
```bash
cd frontend
streamlit run app.py
```

## Variabili d'ambiente necessarie

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=tua_anon_key
```

Su GitHub: Settings → Secrets → Actions → aggiungi le stesse variabili.
Su Streamlit Cloud: Settings → Secrets → stesso formato.
