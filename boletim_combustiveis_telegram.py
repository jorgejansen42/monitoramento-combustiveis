import os
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from dotenv import load_dotenv

# 1. Configurações de Diretório e Fuso Horário
pasta_projeto = Path(__file__).resolve().parent
load_dotenv(dotenv_path=pasta_projeto / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FUSO_BAHIA = ZoneInfo("America/Bahia")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError(f"Verifique TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no arquivo: {pasta_projeto / '.env'}")

# 2. Mapa das Principais Cidades da Bahia, Bandeira Mais Atraente na Rota e Estrutura de Café/Conveniência
RECOMENDACAO_POSTOS_BA = {
    "Salvador": {
        "bandeira": "Rede Menor Preço / Postos Ipiranga (Av. Paralela e BR-324)",
        "conveniencia": "AM/PM completa — café expresso, pão de queijo na hora e área climatizada"
    },
    "Camaçari": {
        "bandeira": "Postos Shell / Rede Larco (Via Parafuso / Polo)",
        "conveniencia": "Shell Select — ótimo café coado/expresso e salgados rápidos"
    },
    "Feira de Santana": {
        "bandeira": "Postos São Gonçalo / Rede Shell (Entronc. BR-324 / BR-116)",
        "conveniencia": "Conveniência 24h completa — parada obrigatória para café e banheiro limpo"
    },
    "Alagoinhas": {
        "bandeira": "Rede Postos Petrobras / Larco (BR-101 — polo mais barato da BA)",
        "conveniencia": "BR Mania — café expresso e lanches regionais (beiju/bolo)"
    },
    "Vitória da Conquista": {
        "bandeira": "Rede Postos Shell / Ipiranga (Anel Rodoviário BR-116)",
        "conveniencia": "Select / AM/PM — café quente perfeito para o friozinho da serra"
    },
    "Barreiras": {
        "bandeira": "Rede Postos Mimosa / Petrobras (BR-242)",
        "conveniencia": "BR Mania / Lanchonete de estrada — café forte e estrutura ampla para frota"
    },
    "Juazeiro": {
        "bandeira": "Postos Shell / Rede Grande Rio (BR-407)",
        "conveniencia": "Shell Select climatizada — café gelado ou expresso e wifi"
    },
    "Ilhéus": {
        "bandeira": "Postos Ipiranga / Rede Gabriela (Rodovia Ilhéus-Itabuna)",
        "conveniencia": "AM/PM — café expresso e parada rápida"
    },
    "Porto Seguro": {
        "bandeira": "Rede Postos Petrobras / Cabral (BR-367)",
        "conveniencia": "BR Mania — café e lanches antes de pegar a BR-101"
    },
    "Teixeira de Freitas": {
        "bandeira": "Rede Postos Capixaba / Shell (BR-101)",
        "conveniencia": "Conveniência 24h com café e restaurante de apoio"
    }
}


def gerar_boletim_resumido() -> str:
    """Lê o combustiveis_bahia_atual.json e monta o boletim executivo para Telegram."""
    arquivo_json = pasta_projeto / "combustiveis_bahia_atual.json"
    if not arquivo_json.exists():
        raise FileNotFoundError(
            "Arquivo 'combustiveis_bahia_atual.json' não encontrado! Rode o monitor_combustiveis_ba.py primeiro."
        )

    with open(arquivo_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    data_ref = dados.get("data_atualizacao", datetime.now(FUSO_BAHIA).strftime("%d/%m/%Y %H:%M"))
    resumo = dados.get("resumo_mercado_ba", {})
    municipios = dados.get("tabela_precos_municipios", [])

    linhas = [
        "⛽ *BOLETIM DE VALORES DE COMBUSTÍVEIS — BAHIA*",
        f"📅 _Atualizado em: {data_ref}_",
        f"📊 *Média BA:* Gasolina R$ {resumo.get('media_estado_gasolina', 0):.2f} | Diesel S10 R$ {resumo.get('media_estado_diesel_s10', 0):.2f}",
        "",
        "📍 *ONDE ABASTECER E TOMAR AQUELE CAFÉ HOJE:*"
    ]

    for item in municipios:
        cidade = item.get("cidade")
        if cidade in RECOMENDACAO_POSTOS_BA:
            info_posto = RECOMENDACAO_POSTOS_BA[cidade]
            gas = item.get("gasolina_comum", 0.0)
            eta = item.get("etanol", 0.0)
            s10 = item.get("diesel_s10", 0.0)
            vantagem = item.get("combustivel_leve_vantajoso", "Gasolina")

            linhas.append(f"\n🏙️ *{cidade}*")
            linhas.append(f"• *Valores:* Gas. R$ {gas:.2f} | Etanol R$ {eta:.2f} | S10 R$ {s10:.2f} _(Melhor leve: {vantagem})_")
            linhas.append(f"• *Rede atraente:* {info_posto['bandeira']}")
            linhas.append(f"• ☕ *Parada:* {info_posto['conveniencia']}")

    linhas.append("\n✅ _Boa rota e bom café!_")
    return "\n".join(linhas)


def enviar_telegram_silencioso(mensagem: str):
    """Envia o boletim direto para o grupo do Telegram em segundo plano."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown"
    }

    try:
        print("Enviando Boletim de Valores de Combustíveis para o Telegram...")
        resp = requests.post(url, json=payload, timeout=20)
        if resp.status_code == 400:
            payload.pop("parse_mode")
            resp = requests.post(url, json=payload, timeout=20)
        resp.raise_for_status()
        print("Sucesso! Boletim enviado para o seu Telegram.")
    except Exception as e:
        print(f"Erro ao enviar no Telegram: {e}")


if __name__ == "__main__":
    boletim = gerar_boletim_resumido()
    print("\n--- PRÉVIA DO BOLETIM ---\n")
    print(boletim)
    print("\n-------------------------\n")
    enviar_telegram_silencioso(boletim)