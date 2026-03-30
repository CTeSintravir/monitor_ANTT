import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

URL = "https://www.gov.br/antt/pt-br/assuntos/ultimas-noticias/"

# ==============================
# CONFIGURAÇÕES
# ==============================
TELEGRAM_TOKEN = "SEU_TOKEN"
TELEGRAM_CHAT_ID = "SEU_CHAT_ID"

EMAIL_ATIVO = False  # True se quiser usar email

# ==============================
def pegar_noticias():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers)
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
    if not os.path.exists("noticias_salvas.json"):
        return []

    with open("noticias_salvas.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ==============================
def salvar_novas(noticias):
    with open("noticias_salvas.json", "w", encoding="utf-8") as f:
        json.dump(noticias, f, ensure_ascii=False, indent=2)

# ==============================
def enviar_telegram(msg):
    if not TELEGRAM_TOKEN:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg
    })

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

    noticias = pegar_noticias()
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

    salvar_novas(noticias)

# ==============================
if __name__ == "__main__":
    main()
