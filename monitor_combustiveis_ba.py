
import os
import json
import time
import urllib.parse
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Configurações de Diretório (salva exclusivamente dentro da pasta do projeto)
pasta_projeto = Path(__file__).resolve().parent
load_dotenv(dotenv_path=pasta_projeto / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FUSO_BAHIA = ZoneInfo("America/Bahia")

if not GEMINI_API_KEY:
    raise ValueError(f"Chave GEMINI_API_KEY não encontrada! Verifique o arquivo: {pasta_projeto / '.env'}")

# 2. Polos Estratégicos da Bahia (Cidades pesquisadas pela ANP + Territórios de Identidade)
POLOS_COMBUSTIVEIS_BA = [
    {"cidade": "Salvador", "macrorregiao": "Metropolitana", "territorio_identidade": "Metropolitano de Salvador", "eixo_rodoviario": "BR-324 / BA-099", "lat": -12.9714, "lon": -38.5014},
    {"cidade": "Camaçari", "macrorregiao": "Metropolitana", "territorio_identidade": "Metropolitano de Salvador", "eixo_rodoviario": "BA-093 / BA-099", "lat": -12.6996, "lon": -38.3263},
    {"cidade": "Lauro de Freitas", "macrorregiao": "Metropolitana", "territorio_identidade": "Metropolitano de Salvador", "eixo_rodoviario": "BA-099", "lat": -12.8978, "lon": -38.3219},
    {"cidade": "Feira de Santana", "macrorregiao": "Centro-Norte", "territorio_identidade": "Portal do Sertão", "eixo_rodoviario": "BR-324 / BR-116 / BR-101", "lat": -12.2664, "lon": -38.9663},
    {"cidade": "Alagoinhas", "macrorregiao": "Nordeste", "territorio_identidade": "Litoral Norte e Agreste Baiano", "eixo_rodoviario": "BR-101 / BR-110", "lat": -12.1336, "lon": -38.4192},
    {"cidade": "Serrinha", "macrorregiao": "Nordeste", "territorio_identidade": "Território do Sisal", "eixo_rodoviario": "BR-116", "lat": -11.6642, "lon": -39.0075},
    {"cidade": "Paulo Afonso", "macrorregiao": "Nordeste", "territorio_identidade": "Itaparica", "eixo_rodoviario": "BR-110 / BA-210", "lat": -9.4061, "lon": -38.2219},
    {"cidade": "Juazeiro", "macrorregiao": "Norte", "territorio_identidade": "Sertão do São Francisco", "eixo_rodoviario": "BR-407 / BR-235", "lat": -9.4167, "lon": -40.5033},
    {"cidade": "Senhor do Bonfim", "macrorregiao": "Norte", "territorio_identidade": "Piemonte Norte do Itapicuru", "eixo_rodoviario": "BR-407", "lat": -10.4614, "lon": -40.1894},
    {"cidade": "Jacobina", "macrorregiao": "Centro-Norte", "territorio_identidade": "Piemonte da Diamantina", "eixo_rodoviario": "BR-324", "lat": -11.1806, "lon": -40.5183},
    {"cidade": "Irecê", "macrorregiao": "Centro-Norte", "territorio_identidade": "Irecê", "eixo_rodoviario": "BA-052 (Estrada do Feijão)", "lat": -11.3042, "lon": -41.8558},
    {"cidade": "Seabra", "macrorregiao": "Centro-Sul", "territorio_identidade": "Chapada Diamantina", "eixo_rodoviario": "BR-242", "lat": -12.4186, "lon": -41.7719},
    {"cidade": "Barreiras", "macrorregiao": "Oeste", "territorio_identidade": "Bacia do Rio Grande", "eixo_rodoviario": "BR-242 / BR-135", "lat": -12.1439, "lon": -44.9969},
    {"cidade": "Luís Eduardo Magalhães", "macrorregiao": "Oeste", "territorio_identidade": "Bacia do Rio Grande", "eixo_rodoviario": "BR-242 / BR-020", "lat": -12.0967, "lon": -45.7867},
    {"cidade": "Bom Jesus da Lapa", "macrorregiao": "Oeste", "territorio_identidade": "Velho Chico", "eixo_rodoviario": "BR-349 / BA-160", "lat": -13.2550, "lon": -43.4181},
    {"cidade": "Guanambi", "macrorregiao": "Centro-Sul", "territorio_identidade": "Sertão Produtivo", "eixo_rodoviario": "BR-030 / BR-122", "lat": -14.2233, "lon": -42.7814},
    {"cidade": "Brumado", "macrorregiao": "Centro-Sul", "territorio_identidade": "Sertão Produtivo", "eixo_rodoviario": "BR-030 / BA-262", "lat": -14.2036, "lon": -41.6653},
    {"cidade": "Vitória da Conquista", "macrorregiao": "Centro-Sul", "territorio_identidade": "Sudoeste Baiano", "eixo_rodoviario": "BR-116 / BA-262", "lat": -14.8619, "lon": -40.8442},
    {"cidade": "Jequié", "macrorregiao": "Centro-Sul", "territorio_identidade": "Médio Rio de Contas", "eixo_rodoviario": "BR-116 / BR-330", "lat": -13.8578, "lon": -40.0836},
    {"cidade": "Santo Antônio de Jesus", "macrorregiao": "Recôncavo", "territorio_identidade": "Recôncavo", "eixo_rodoviario": "BR-101 / BA-046", "lat": -12.9689, "lon": -39.2614},
    {"cidade": "Valença", "macrorregiao": "Sul", "territorio_identidade": "Baixo Sul (Costa do Dendê)", "eixo_rodoviario": "BA-001", "lat": -13.3703, "lon": -39.0731},
    {"cidade": "Ilhéus", "macrorregiao": "Sul", "territorio_identidade": "Litoral Sul (Costa do Cacau)", "eixo_rodoviario": "BR-415 / BA-001", "lat": -14.7935, "lon": -39.0464},
    {"cidade": "Itabuna", "macrorregiao": "Sul", "territorio_identidade": "Litoral Sul (Costa do Cacau)", "eixo_rodoviario": "BR-101 / BR-415", "lat": -14.7876, "lon": -39.2781},
    {"cidade": "Porto Seguro", "macrorregiao": "Extremo Sul", "territorio_identidade": "Costa do Descobrimento", "eixo_rodoviario": "BR-367 / BR-101", "lat": -16.4435, "lon": -39.0643},
    {"cidade": "Eunápolis", "macrorregiao": "Extremo Sul", "territorio_identidade": "Costa do Descobrimento", "eixo_rodoviario": "BR-101 / BR-367", "lat": -16.3716, "lon": -39.5821},
    {"cidade": "Teixeira de Freitas", "macrorregiao": "Extremo Sul", "territorio_identidade": "Extremo Sul", "eixo_rodoviario": "BR-101 / BA-290", "lat": -17.5399, "lon": -39.7419},
]


def agora_bahia() -> datetime:
    return datetime.now(FUSO_BAHIA)


def buscar_dados_web_combustiveis_ba() -> str:
    """Coleta manchetes e boletins recentes (ANP, Refinaria de Mataripe/Acelen, IPTL) via Google News RSS."""
    consultas = [
        "preço gasolina diesel etanol Bahia ANP levantamento 2026",
        "reajuste combustíveis Refinaria de Mataripe Acelen Bahia 2026",
        "preço médio combustíveis cidades Bahia Salvador Feira de Santana Conquista Juazeiro 2026"
    ]
    resultados = []

    for termo in consultas:
        query = urllib.parse.quote(termo)
        url = f"https://news.google.com/rss/search?q={query}+when:7d&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "xml")
            for item in soup.find_all("item")[:8]:
                titulo = item.title.text if item.title else ""
                pub_date = item.pubDate.text if item.pubDate else ""
                descricao = BeautifulSoup(item.description.text, "html.parser").get_text() if item.description else ""
                resultados.append(f"- [{pub_date}] {titulo} | Resumo: {descricao[:180]}")
        except Exception as e:
            print(f"Aviso na busca '{termo}': {e}")

    return "\n".join(resultados) if resultados else "Sem boletins indexados nos últimos 7 dias."


def gerar_tabela_combustiveis_2026(noticias_web: str) -> dict:
    """Consolida os preços de 2026 por município e Território de Identidade em JSON estruturado."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    data_atual = agora_bahia().strftime("%d/%m/%Y %H:%M")

    prompt = f"""
    Data/Hora da Consulta (Bahia): {data_atual} (Ano de referência: 2026).

    CONTEXTO COLETADO NA WEB (ANP / Refinaria de Mataripe Acelen / IPTL):
    {noticias_web}

    LISTA DE MUNICÍPIOS-POLO E TERRITÓRIOS DA BAHIA:
    {json.dumps(POLOS_COMBUSTIVEIS_BA, ensure_ascii=False)}

    Atue como um Analista de Custos de Frota e Inteligência de Suprimentos na Bahia.
    Com base nos levantamentos mais recentes da ANP e movimentações da Refinaria de Mataripe (Acelen) em 2026:
    1. Consolide os preços médios atualizados (em R$/litro) de Gasolina Comum, Gasolina Aditivada, Etanol Hidratado, Diesel S10 e Diesel S500 para TODOS os {len(POLOS_COMBUSTIVEIS_BA)} municípios-polo listados acima, respeitando a logística regional da Bahia (polos próximos à refinaria como Alagoinhas, Feira de Santana e Salvador têm menor custo de frete; Extremo Sul, Oeste e Norte têm acréscimo logístico).
    2. Calcule os indicadores comparativos para orientar onde abastecer a frota com melhor custo-benefício.

    Retorne EXCLUSIVAMENTE um JSON válido (sem blocos ```json) com a estrutura exata abaixo:

    {{
      "data_atualizacao": "{data_atual}",
      "ano_referencia": 2026,
      "fonte_principal": "ANP (LPC) / Refinaria de Mataripe (Acelen) / Monitoramento Web",
      "resumo_mercado_ba": {{
        "media_estado_gasolina": 6.64,
        "media_estado_etanol": 4.61,
        "media_estado_diesel_s10": 7.59,
        "ultimo_movimento_refinaria": "Resumo curto sobre o último reajuste (alta/queda) na Refinaria de Mataripe",
        "melhor_polo_diesel_s10": "Nome da cidade mais barata para Diesel S10",
        "melhor_polo_gasolina": "Nome da cidade mais barata para Gasolina"
      }},
      "tabela_precos_municipios": [
        {{
          "cidade": "Nome exato da lista",
          "macrorregiao": "Macrorregiao exata da lista",
          "territorio_identidade": "Territorio exato da lista",
          "eixo_rodoviario": "Eixo exato da lista",
          "latitude": -12.9714,
          "longitude": -38.5014,
          "gasolina_comum": 6.55,
          "gasolina_aditivada": 6.72,
          "etanol": 4.69,
          "diesel_s10": 7.74,
          "diesel_s500": 7.62,
          "relacao_etanol_gasolina_pct": 71.6,
          "combustivel_leve_vantajoso": "Gasolina | Etanol",
          "spread_diesel_vs_media_ba": 0.15,
          "classificacao_custo_abastecimento": "Econômico (Abastecer Aqui) | Na Média | Caro (Evitar se Possível)",
          "variacao_semanal_pct": -0.5
        }}
      ]
    }}
    """

    modelos = ["gemini-flash-latest", "gemini-pro-latest", "gemma-3-27b-it"]
    try:
        disponiveis = [
            m.name.replace("models/", "") for m in client.models.list()
            if ("gemini" in m.name or "gemma" in m.name) and "embedding" not in m.name and "vision" not in m.name
        ]
        if disponiveis:
            disponiveis.sort(key=lambda x: (0 if "flash" in x else (1 if "gemma" in x else 2)))
            modelos = disponiveis
    except Exception:
        pass

    for modelo in modelos:
        try:
            print(f"Consolidando tabela de combustíveis 2026 com {modelo}...")
            response = client.models.generate_content(
                model=modelo,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1),
            )
            texto_limpo = response.text.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(texto_limpo)
        except Exception as e:
            print(f"Aviso com {modelo}: {str(e)[:120]}...")
            time.sleep(2)

    raise RuntimeError("Não foi possível consolidar os preços de combustíveis no momento.")


def salvar_arquivos_json(dados: dict):
    """Salva o JSON atual e o histórico diário exclusivamente dentro da pasta do projeto."""
    # 1. Arquivo principal sempre atualizado (para o Power BI / GitHub)
    arquivo_atual = pasta_projeto / "combustiveis_bahia_atual.json"
    with open(arquivo_atual, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    # 2. Pasta interna de histórico diário dentro do próprio projeto
    pasta_historico = pasta_projeto / "historico_diario"
    pasta_historico.mkdir(exist_ok=True)
    data_str = agora_bahia().strftime("%Y-%m-%d")
    arquivo_historico = pasta_historico / f"combustiveis_{data_str}.json"
    with open(arquivo_historico, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    print(f"Sucesso! Arquivos salvos em:\n- {arquivo_atual}\n- {arquivo_historico}")


if __name__ == "__main__":
    print("1. Pesquisando cotações de combustíveis na Bahia (2026)...")
    noticias = buscar_dados_web_combustiveis_ba()

    print("2. Estruturando tabela por Território de Identidade e Município...")
    tabela_2026 = gerar_tabela_combustiveis_2026(noticias)

    print("3. Salvando JSON atual e histórico diário...")
    salvar_arquivos_json(tabela_2026)
    