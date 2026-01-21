# 🚀 GitHub Actions Setup Guide

Il bot è configurato per eseguirsi **automaticamente ogni 30 minuti** usando GitHub Actions!

## 🔒 Step 1: Configura i Secrets (Opzionale)

Se vuoi ricevere notifiche Discord o Telegram, devi aggiungere i webhook ai GitHub Secrets:

### Per Discord:
1. Vai su **https://github.com/alessandroferraraaa/VINTED-ULTIMO-TEST/settings/secrets/actions**
2. Clicca **"New repository secret"**
3. Crea un secret chiamato `DISCORD_WEBHOOK_URL`
4. Incolla l'URL del tuo webhook Discord
5. Clicca **"Add secret"**

### Per Telegram:
1. Ripeti i passaggi sopra per creare due nuovi secrets:
   - `TELEGRAM_BOT_TOKEN` = Token da BotFather
   - `TELEGRAM_CHAT_ID` = Il tuo Chat ID

## 📊 Cosa Succede

Ogni 30 minuti:
1. GitHub Actions avvia un workflow
2. Il bot scarica il codice dal repository
3. Installa le dipendenze (`requests`)
4. Esegue il monitoraggio su Vinted
5. Invia notifiche Discord/Telegram (se configurate)
6. Salva il database e i log come artifacts

## 📁 Visualizzare i Log

1. Vai su **https://github.com/alessandroferraraaa/VINTED-ULTIMO-TEST/actions**
2. Clicca su un workflow eseguito
3. Guarda i log in tempo reale
4. Scarica i artifacts (database + log) dal tab **"Artifacts"**

## 🛡️ Mantenere il Workflow Aggiornato

Se modifichi il codice principale (`vinted_bot.py`), il workflow userà automaticamente la versione più recente.

### Per eseguire il bot manualmente:
1. Vai su **Actions** → **"Vinted Bot Monitor"**
2. Clicca **"Run workflow"** → **"Run workflow"**

## 🗒️ Personalizzare l'Intervallo

Per cambiare la frequenza d'esecuzione:
1. Apri `.github/workflows/vinted_bot.yml`
2. Modifica la riga con `cron: '*/30 * * * *'`:
   - `*/15 * * * *` = Ogni 15 minuti
   - `*/60 * * * *` = Ogni ora
   - `0 * * * *` = Ogni ora (minuto 0)
   - `0 */6 * * *` = Ogni 6 ore

## ⚠️ Note Importanti

- \u2705 **GitHub Actions è GRATUITO** per repository pubblici
- \u2705 Il workflow usa **Ubuntu** per eseguire il bot
- \u2705 La freccia temporale è **UTC**, non l'ora locale
- ❌ **Attenzione**: I log contengono dati sensibili (webhook), scaricali in privato!

## 🔍 Troubleshooting

**Il workflow non parte?**
- Verifica che il file `.github/workflows/vinted_bot.yml` esista
- Vai su Actions e attiva i workflow se disabilitati
- Controlla che `requirements.txt` contenga `requests==2.31.0`

**Notifiche non arrivano?**
- Verifica che i secrets siano correttamente configurati
- Controlla i log del workflow per errori
- Assicurati che il webhook Discord/Telegram sia ancora valido

**Il database non persiste?**
- GitHub Actions crea un nuovo ambiente per ogni esecuzione
- Il database viene salvato come artifact per 7 giorni
- Se vuoi persistenza, usa un servizio esterno (AWS S3, Azure, etc.)

---

**Il bot è ora completamente autonomo! 🤖**
