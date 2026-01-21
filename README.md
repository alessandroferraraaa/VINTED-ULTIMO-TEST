# 🔍⚽ VINTED FOOTBALL TRACKSUIT BOT

**Monitor in tempo reale le tute da calcio complete per adulti su Vinted**

Bot Python rigoroso e affidabile che filtra le inserzioni Vinted per trovare SOLO tute da calcio complete (felpa + pantalone lungo) per adulti, con notifiche Discord/Telegram in tempo reale.

## ✍️ Caratteristiche Principali

### ✅ Filtri Stringenti
- **Taglie**: Solo **S, M, L, XL** (rigidissimo, esclude bambino)
- **Composizione**: SOLO felpa + pantalone lungo
  - ❌ Esclude tute estive
  - ❌ Esclude maglia + short
  - ❌ Esclude kit gara, academy, training
  - ❌ Esclude pezzi singoli
- **Squadre approvate**: Liverpool, Manchester City, Olympique Marsiglia, Lione, PSG, Borussia Dortmund, Bayern Monaco, Inter, Manchester United, Nazionale Argentina, Nazionale Francia, Nazionale Spagna, Arsenal, Tottenham, Real Madrid, Barcellona, Atlético Madrid, Chelsea
- **Marche**: Nike, Adidas, Puma, Lotto, Reebok, Umbro, Kappa
- **Condizioni**: "Ottime condizioni", "Nuovo senza cartellino", "Nuovo con cartellino"

### 🗒️ Parole Vietate
Il bot esclude automaticamente annunci che contengono:
- `solo pantalone`, `solo felpa`, `joggers`, `short`, `shorts`, `maillot`
- `kids`, `junior`, `academy`, `enfant`, `garçon`, `bambino`
- `anni`, `mesi`, `cm`, `age`, `child`, `youth`
- `summer`, `estivo`, `tees`, `polo`, `shirt`, `maglietta`

### 🔍 Database & Logging
- **SQLite** per tracciamento completo
- Registra ogni inserzione trovata, approvata o scartata
- Motivo del rifiuto dettagliato
- Log file con timestamp
- Evita duplicati automaticamente

### 🔔 Notifiche Tempo Reale
- **Discord Webhook**: Embed con immagine, prezzo, squadra, brand, taglia, ID, orario di pubblicazione
- **Telegram Bot**: Notifiche formattate con link diretto
- Entrambi opzionali (configurabili nel `CONFIG`)

### ⚡ Affidabilità
- Gestione automatica rate limit
- Retry su timeout
- Sessione HTTP persistente
- Ricerca multi-URL (IT, DE, FR, ES, NL, BE)
- Ordinamento sempre dal più recente

---

## 🚀 Quick Start

### 1. Clone la repository
```bash
git clone https://github.com/alessandroferraraaa/VINTED-ULTIMO-TEST.git
cd VINTED-ULTIMO-TEST
```

### 2. Installa le dipendenze
```bash
pip install -r requirements.txt
```

### 3. Configura i webhook (opzionale)

#### Discord Webhook:
1. Vai nel tuo server Discord
2. **Impostazioni Server** → **Integrazioni** → **Webhook**
3. Clicca **Crea Webhook**
4. Dai un nome (es. "Vinted Bot")
5. Scegli il canale
6. Copia l'URL del webhook
7. Apri `vinted_bot.py` e incolla l'URL in `CONFIG["DISCORD_WEBHOOK_URL"]`

#### Telegram Bot:
1. Su Telegram, cercha `@BotFather`
2. Crea un nuovo bot con `/newbot`
3. Copia il token
4. Ottieni il tuo Chat ID:
   - Cercha `@userinfobot`
   - Scrivi `/start`
   - Ti darà il tuo ID
5. Apri `vinted_bot.py` e configura:
   - `CONFIG["TELEGRAM_BOT_TOKEN"]` = il token di BotFather
   - `CONFIG["TELEGRAM_CHAT_ID"]` = il tuo Chat ID

### 4. Avvia il bot
```bash
python vinted_bot.py
```

**Il bot inizierà a monitorare automaticamente ogni 60 secondi!**

---

## 📊 File di Output

- **`vinted_bot.db`**: Database SQLite con tutte le inserzioni
  - Tabella `items`: Ogni inserzione trovata/scartata
  - Tabella `notified`: Tracking notifiche inviate
- **`vinted_bot.log`**: Log dettagliato di ogni ciclo

## 🔧 Personalizzazione

### Modificare frequenza di controllo:
```python
CONFIG["CHECK_INTERVAL"] = 30  # in secondi (default 60)
```

### Aggiungere altre squadre:
```python
APPROVED_TEAMS.add("nome squadra")
```

### Aggiungere altri marchi:
```python
APPROVED_BRANDS.add("brand name")
```

### Disabilitare Telegram/Discord:
```python
CONFIG["DISCORD_WEBHOOK_URL"] = ""  # Lascia vuoto per disabilitare
```

---

## 🔑 Struttura del Codice

```
vinted_bot.py
├─ CONFIG: Configurazione centrale
├─ APPROVED_TEAMS, APPROVED_BRANDS: Whitelist
├─ FORBIDDEN_KEYWORDS: Blacklist
├─ init_database(): Inizializzazione DB
├─ check_size(), check_forbidden_keywords(): Validazioni
├─ is_complete_tracksuit(): Validazione completa
├─ fetch_vinted_items(): API call a Vinted
├─ send_discord_notification(): Notifiche Discord
├─ send_telegram_notification(): Notifiche Telegram
└─ monitor_vinted(): Loop principale
```

---

## ⚠️ Importante

- **Nessun storage locale pericoloso**: Non usa `localStorage` o `sessionStorage`
- **Database SQLite**: Tutto tracciato localmente
- **Zero rate limit issues**: Gestione automatica del rate limit di Vinted
- **Affidabile**: Produzione-ready, nessun placeholder

---

## 🙋 Support

Se hai problemi o vuoi aggiungere feature:
1. Apri un **Issue** su GitHub
2. Descrivi il comportamento desiderato
3. Allega i log da `vinted_bot.log`

---

## 📄 License

MIT License - Libero di usare, modificare, distribuire

---

**Made with ❤️ by alessandroferraraaa**

💖 Se il bot ti è utile, lascia una ★ star!
