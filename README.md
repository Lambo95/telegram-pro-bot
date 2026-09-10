\# Telegram PRO Stop Loss Bot



Bot Telegram per calcolo bancata, P\&L e gestione stop loss con:



\- Pulsanti variazione quota (+15%, +30%, +50%)

\- Pulsanti recupero (25%, 50%, 75%)

\- Conversazione guidata

\- Calcolo bancata e P\&L

\- Suggerimento puntata/bancata



\## Deploy su Render



1\. Crea un repo GitHub con questi file

2\. Vai su https://render.com

3\. New → Web Service

4\. Seleziona il repo

5\. Imposta la variabile ambiente:

&#x20;  - TELEGRAM\_TOKEN=il\_token\_del\_tuo\_bot

6\. Deploy



\## Webhook Telegram



Imposta il webhook:



`https://api.telegram.org/botTUO\_TOKEN/setWebhook?url=URL\_DEL\_SERVIZIO\_RENDER`



