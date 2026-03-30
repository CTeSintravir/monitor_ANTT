import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

URL = "https://www.gov.br/antt/pt-br/assuntos/ultimas-noticias/"

# ==============================
# CONFIG (via Secrets)
# ==============================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

EMAIL_ATIVO = True
EMAIL_REMETENTE = os.getenv("EMAIL_USER")
EMAIL_SENHA = os.getenv("EMAIL_PASS")
EMAIL_DESTINO = "coordenador@cte-sintravir.com.br"
SMTP_SERVIDOR = "smtp.gmail.com"
SMTP_PORTA = 587

ARQUIVO_DB = "noticias_salvas.json"

# ==============================
def pegar_noticias():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    noticias = []

    itens = soup.find_all("li")

    for item in itens:
        categoria = item.find("strong")
        titulo = item.find("a")
        descricao = item.find("span")

        if not titulo:
            continue

        cat = categoria.text.strip() if categoria else "SEM CATEGORIA"
        titulo_texto = titulo.text.strip()
        link = titulo.get("href")

        if link and not link.startswith("http"):
            link = "https://www.gov.br" + link

        desc = descricao.text.strip() if descricao else ""

        noticias.append({
            "categoria": cat,
            "titulo": titulo_texto,
            "descricao": desc,
            "link": link
        })

    return noticias

# ==============================
def carregar_antigas():
    if not os.path.exists(ARQUIVO_DB):
        return []

    with open(ARQUIVO_DB, "r", encoding="utf-8") as f:
        return json.load(f)

# ==============================
def salvar_novas(noticias):
    with open(ARQUIVO_DB, "w", encoding="utf-8") as f:
        json.dump(noticias, f, ensure_ascii=False, indent=2)

# ==============================
def enviar_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram não configurado.")
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg
        }, timeout=10)

        print("Telegram enviado!")

    except Exception as e:
        print("Erro Telegram:", e)

# ==============================
def enviar_email(msg):
    if not EMAIL_ATIVO or not EMAIL_REMETENTE or not EMAIL_SENHA:
        print("Email não configurado.")
        return

    try:
        mensagem = MIMEText(msg, "plain", "utf-8")
        mensagem["Subject"] = "🚨 Nova notícia ANTT"
        mensagem["From"] = EMAIL_REMETENTE
        mensagem["To"] = EMAIL_DESTINO

        with smtplib.SMTP(SMTP_SERVIDOR, SMTP_PORTA) as server:
            server.starttls()
            server.login(EMAIL_REMETENTE, EMAIL_SENHA)
            server.send_message(mensagem)

        print("Email enviado!")

    except Exception as e:
        print("Erro Email:", e)

# ==============================
def formatar_noticia(n):
    return f"""🚨 NOVA NOTÍCIA ANTT

{n['categoria']}
{n['titulo']}
{n['descricao']}
{n['link']}
"""

# ==============================
def main():
    print(f"[{datetime.now()}] Verificando ANTT...")

    try:
        noticias = pegar_noticias()
    except Exception as e:
        print("Erro ao acessar site:", e)
        return

    antigas = carregar_antigas()
    links_antigos = {n["link"] for n in antigas}

    novas = [n for n in noticias if n["link"] not in links_antigos]

    if not novas:
        print("Nenhuma notícia nova.")
        return

    print(f"{len(novas)} novas encontradas!")

    for n in novas:
        msg = formatar_noticia(n)
        print(msg)
        enviar_telegram(msg)
        enviar_email(msg)

    salvar_novas(noticias)

# ==============================
if __name__ == "__main__":
    main()
