# ⚡ GitHub Actions Setup - Vinted Bot

## 🚀 Il workflow è già creato!

Trovalo qui: `.github/workflows/vinted-bot.yml`

---

## 📋 SETUP FINALE (3 minuti)

### Step 1: Aggiungi i Secrets su GitHub

1. Vai al tuo repo su GitHub
2. Clicca su **Settings** (in alto a destra)
3. Seleziona **Secrets and variables** (sidebar sinistra)
4. Clicca su **Actions**
5. Clicca **New repository secret**

Aggiungi questi secrets (opzionali):

#### Secret 1: Discord Webhook (OPZIONALE)
```
Name: DISCORD_WEBHOOK_URL
Value: https://discordapp.com/api/webhooks/YOUR_WEBHOOK_URL
```

#### Secret 2: Telegram Bot Token (OPZIONALE)
```
Name: TELEGRAM_BOT_TOKEN
Value: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
```

#### Secret 3: Telegram Chat ID (OPZIONALE)
```
Name: TELEGRAM_CHAT_ID
Value: 987654321
```

> Se non hai Discord/Telegram, **non aggiungere nulla** - il bot funziona lo stesso!

---

### Step 2: Esegui il Workflow

1. Vai a **Actions** (nel menu in alto del repo)
2. Seleziona **🤖 Vinted Football Bot Monitor** (sulla sinistra)
3. Clicca **Run workflow** (pulsante verde)
4. Clicca di nuovo **Run workflow** nella popup

**FATTO!** Il bot parte in ~2 minuti.

---

## 🔄 Come Funziona

### ⏳ Schedule Automatico

Il workflow si esegue automaticamente **ogni ora** grazie a:

```yaml
schedule:
  - cron: '0 * * * *'  # Ogni ora alle :00
```

#### Cambiare la frequenza:

**Ogni 30 minuti:**
```yaml
  - cron: '*/30 * * * *'
```

**Ogni 6 ore:**
```yaml
  - cron: '0 */6 * * *'
```

**Ogni giorno alle 09:00:**
```yaml
  - cron: '0 9 * * *'
```

> Usa [crontab.guru](https://crontab.guru) per creare la tua schedule!

---

## 📊 Che succede durante l'esecuzione

### Timeline:

```
1. Runner Ubuntu parte (~10 sec)
2. Checkout del codice (~5 sec)
3. Setup Python 3.11 (~15 sec)
4. Install dependencies [pip install...] (~30 sec)
5. Setup Chrome + ChromeDriver (~20 sec)
6. Run vinted_bot.py
   ⭐ Bot apre browser headless
   ⭐ Scrapa Vinted
   ⭐ Filtra con le tue regole
   ⭐ Invia notifiche Discord/Telegram
   ⭐ Salva in DB
7. Job finito (~3-5 minuti totali)
```

---

## 💽 Log e Artifacts

### Vedi i log in real-time:

1. **Actions** → seleziona il run
2. Clicca su **Run Vinted Bot**
3. Vedi l'output in tempo reale

### Scarica i log:

Se il bot fallisce, puoi scaricare `vinted_bot.log` come artifact:

1. **Actions** → seleziona il run fallito
2. Scroll down a **Artifacts**
3. Download `vinted-bot-logs`

Gli artifacts vengono mantenuti per **7 giorni**.

---

## ❌ Troubleshooting

### Errore: "ModuleNotFoundError: No module named 'selenium'"

**Causa:** Il workflow non ha installato le dipendenze correttamente.

**Soluzione:**
- Assicurati che `requirements.txt` esiste nel root del repo
- Contiene: `selenium>=4.15.0` e `requests>=2.31.0`

### Errore: "ChromeDriver not found"

**Causa:** Chrome non è installato nel runner.

**Soluzione:** Il workflow già include `setup-chrome@latest` - dovrebbe funzionare.
Se no, prova a disabilitare il timeout: cambia `timeout-minutes: 10` in `timeout-minutes: 15`

### Il bot non invia notifiche Discord/Telegram

**Causa:** Secret non configurato o URL errato.

**Soluzione:**
1. Verifica che i secrets siano aggiunti correttamente
2. Testa manualmente il webhook Discord/Telegram bot
3. Controlla i log del workflow

### Il bot non trova item

**Causa:** Vinted ha cambiato struttura HTML o bot non starta.

**Soluzione:**
1. Verifica che Selenium funzioni (log dovrebbe dire "Selenium driver initialized")
2. Controlla i filtri in `vinted_bot.py` (APPROVED_TEAMS, APPROVED_BRANDS, ALLOWED_SIZES)
3. Aumenta il timeout: `timeout-minutes: 15` o `timeout-minutes: 20`

---

## 🔓 Secrets sicuri

I secrets **non vengono mai loggati** in GitHub Actions:
- Non appaiono nei log
- Non vengono salvati in artifact
- Sono criptati in GitHub

Puoi fidarti! 🔐

---

## 🚀 Prossimi Step

1. **Aggiungi i secrets** (5 minuti)
2. **Esegui il workflow manualmente** (clicca Run workflow)
3. **Aspetta ~5 minuti** che finisca
4. **Controlla i log** per verificare che funzioni
5. **Configura la schedule** a tuo piacimento

**Fatto!** Il bot ora gira su GitHub Actions ogni ora! ⚡

---

## 📚 Referenze

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Cron Syntax](https://crontab.guru)
- [Selenium Python Docs](https://selenium-python.readthedocs.io/)
- [Vinted API](https://www.vinted.it) (web scraping)

---

**Domande?** Controlla i log del workflow! 📊
