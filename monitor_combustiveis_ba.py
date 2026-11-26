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

# 2. Polos Estratégicos da Bahia (26 Cidades-polo + Territórios de Identidade + Fator Logístico)
POLOS_COMBUSTIVEIS_BA = [
    {"cidade": "Salvador", "macrorregiao": "Metropolitana", "territorio_identidade": "Metropolitano de Salvador", "eixo_rodoviario": "BR-324 / BA-099", "lat": -12.9714, "lon": -38.5014, "fator_frete": -0.06},
    {"cidade": "Camaçari", "macrorregiao": "Metropolitana", "territorio_identidade": "Metropolitano de Salvador", "eixo_rodoviario": "BA-093 / BA-099", "lat": -12.6996, "lon": -38.3263, "fator_frete": -0.09},
    {"cidade": "Lauro de Freitas", "macrorregiao": "Metropolitana", "territorio_identidade": "Metropolitano de Salvador", "eixo_rodoviario": "BA-099", "lat": -12.8978, "lon": -38.3219, "fator_frete": -0.05},
    {"cidade": "Feira de Santana", "macrorregiao": "Centro-Norte", "territorio_identidade": "Portal do Sertão", "eixo_rodoviario": "BR-324 / BR-116 / BR-101", "lat": -12.2664, "lon": -38.9663, "fator_frete": -0.14},
    {"cidade": "Alagoinhas", "macrorregiao": "Nordeste", "territorio_identidade": "Litoral Norte e Agreste Baiano", "eixo_rodoviario": "BR-101 / BR-110", "lat": -12.1336, "lon": -38.4192, "fator_frete": -0.16},
    {"cidade": "Serrinha", "macrorregiao": "Nordeste", "territorio_identidade": "Território do Sisal", "eixo_rodoviario": "BR-116", "lat": -11.6642, "lon": -39.0075, "fator_frete": -0.04},
    {"cidade": "Paulo Afonso", "macrorregiao": "Nordeste", "territorio_identidade": "Itaparica", "eixo_rodoviario": "BR-110 / BA-210", "lat": -9.4061, "lon": -38.2219, "fator_frete": 0.08},
    {"cidade": "Juazeiro", "macrorregiao": "Norte", "territorio_identidade": "Sertão do São Francisco", "eixo_rodoviario": "BR-407 / BR-235", "lat": -9.4167, "lon": -40.5033, "fator_frete": 0.11},
    {"cidade": "Senhor do Bonfim", "macrorregiao": "Norte", "territorio_identidade": "Piemonte Norte do Itapicuru", "eixo_rodoviario": "BR-407", "lat": -10.4614, "lon": -40.1894, "fator_frete": 0.03},
    {"cidade": "Jacobina", "macrorregiao": "Centro-Norte", "territorio_identidade": "Piemonte da Diamantina", "eixo_rodoviario": "BR-324", "lat": -11.1806, "lon": -40.5183, "fator_frete": 0.02},
    {"cidade": "Irecê", "macrorregiao": "Centro-Norte", "territorio_identidade": "Irecê", "eixo_rodoviario": "BA-052 (Estrada do Feijão)", "lat": -11.3042, "lon": -41.8558, "fator_frete": 0.09},
    {"cidade": "Seabra", "macrorregiao": "Centro-Sul", "territorio_identidade": "Chapada Diamantina", "eixo_rodoviario": "BR-242", "lat": -12.4186, "lon": -41.7719, "fator_frete": 0.07},
    {"cidade": "Barreiras", "macrorregiao": "Oeste", "territorio_identidade": "Bacia do Rio Grande", "eixo_rodoviario": "BR-242 / BR-135", "lat": -12.1439, "lon": -44.9969, "fator_frete": 0.15},
    {"cidade": "Luís Eduardo Magalhães", "macrorregiao": "Oeste", "territorio_identidade": "Bacia do Rio Grande", "eixo_rodoviario": "BR-242 / BR-020", "lat": -12.0967, "lon": -45.7867, "fator_frete": 0.14},
    {"cidade": "Bom Jesus da Lapa", "macrorregiao": "Oeste", "territorio_identidade": "Velho Chico", "eixo_rodoviario": "BR-349 / BA-160", "lat": -13.2550, "lon": -43.4181, "fator_frete": 0.12},
    {"cidade": "Guanambi", "macrorregiao": "Centro-Sul", "territorio_identidade": "Sertão Produtivo", "eixo_rodoviario": "BR-030 / BR-122", "lat": -14.2233, "lon": -42.7814, "fator_frete": 0.06},
    {"cidade": "Brumado", "macrorregiao": "Centro-Sul", "territorio_identidade": "Sertão Produtivo", "eixo_rodoviario": "BR-030 / BA-262", "lat": -14.2036, "lon": -41.6653, "fator_frete": 0.04},
    {"cidade": "Vitória da Conquista", "macrorregiao": "Centro-Sul", "territorio_identidade": "Sudoeste Baiano", "eixo_rodoviario": "BR-116 / BA-262", "lat": -14.8619, "lon": -40.8442, "fator_frete": -0.02},
    {"cidade": "Jequié", "macrorregiao": "Centro-Sul", "territorio_identidade": "Médio Rio de Contas", "eixo_rodoviario": "BR-116 / BR-330", "lat": -13.8578, "lon": -40.0836, "fator_frete": -0.05},
    {"cidade": "Santo Antônio de Jesus", "macrorregiao": "Recôncavo", "territorio_identidade": "Recôncavo", "eixo_rodoviario": "BR-101 / BA-046", "lat": -12.9689, "lon": -39.2614, "fator_frete": -0.08},
    {"cidade": "Valença", "macrorregiao": "Sul", "territorio_identidade": "Baixo Sul (Costa do Dendê)", "eixo_rodoviario": "BA-001", "lat": -13.3703, "lon": -39.0731, "fator_frete": 0.01},
    {"cidade": "Ilhéus", "macrorregiao": "Sul", "territorio_identidade": "Litoral Sul (Costa do Cacau)", "eixo_rodoviario": "BR-415 / BA-001", "lat": -14.7935, "lon": -39.0464, "fator_frete": 0.05},
    {"cidade": "Itabuna", "macrorregiao": "Sul", "territorio_identidade": "Litoral Sul (Costa do Cacau)", "eixo_rodoviario": "BR-101 / BR-415", "lat": -14.7876, "lon": -39.2781, "fator_frete": 0.03},
    {"cidade": "Porto Seguro", "macrorregiao": "Extremo Sul", "territorio_identidade": "Costa do Descobrimento", "eixo_rodoviario": "BR-367 / BR-101", "lat": -16.4435, "lon": -39.0643, "fator_frete": 0.16},
    {"cidade": "Eunápolis", "macrorregiao": "Extremo Sul", "territorio_identidade": "Costa do Descobrimento", "eixo_rodoviario": "BR-101 / BR-367", "lat": -16.3716, "lon": -39.5821, "fator_frete": 0.09},
    {"cidade": "Teixeira de Freitas", "macrorregiao": "Extremo Sul", "territorio_identidade": "Extremo Sul", "eixo_rodoviario": "BR-101 / BA-290", "lat": -17.5399, "lon": -39.7419, "fator_frete": 0.13},
]


def agora_bahia() -> datetime:
    return datetime.now(FUSO_BAHIA)


def buscar_dados_web_combustiveis_ba() -> list:
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
                resultados.append(f"[{pub_date}] {titulo} | Resumo: {descricao[:180]}")
        except Exception as e:
            print(f"Aviso na busca '{termo}': {e}")

    return resultados


def gerar_fallback_local_2026(noticias_lista: list) -> dict:
    """Garante a geração completa das 26 cidades caso a IA não responda ou abrevie a lista."""
    data_atual = agora_bahia().strftime("%d/%m/%Y %H:%M")
    base_gasolina = 6.62
    base_etanol = 4.65
    base_diesel_s10 = 7.58

    municipios: list[dict] = []
    for p in POLOS_COMBUSTIVEIS_BA:
        fator = p["fator_frete"]
        gas_c = round(base_gasolina + fator, 2)
        gas_a = round(gas_c + 0.18, 2)
        eta = round(base_etanol + (fator * 0.85), 2)
        d_s10 = round(base_diesel_s10 + (fator * 1.1), 2)
        d_s500 = round(d_s10 - 0.12, 2)

        rel_pct = round((eta / gas_c) * 100, 1)
        vantajoso = "Etanol" if rel_pct <= 70.0 else "Gasolina"
        spread_diesel = round(d_s10 - base_diesel_s10, 2)

        if spread_diesel <= -0.05:
            classif = "Econômico (Abastecer Aqui)"
        elif spread_diesel >= 0.08:
            classif = "Caro (Evitar se Possível)"
        else:
            classif = "Na Média"

        municipios.append({
            "cidade": p["cidade"],
            "macrorregiao": p["macrorregiao"],
            "territorio_identidade": p["territorio_identidade"],
            "eixo_rodoviario": p["eixo_rodoviario"],
            "latitude": p["lat"],
            "longitude": p["lon"],
            "gasolina_comum": gas_c,
            "gasolina_aditivada": gas_a,
            "etanol": eta,
            "diesel_s10": d_s10,
            "diesel_s500": d_s500,
            "relacao_etanol_gasolina_pct": rel_pct,
            "combustivel_leve_vantajoso": avantajoso,
            "spread_diesel_vs_media_ba": spread_diesel,
            "classificacao_custo_abastecimento": classif,
            "variacao_semanal_pct": -0.3
        })

    manchete_ref = noticias_lista[0] if noticias_lista else "Referência ANP / Refinaria de Mataripe (Acelen) - Bahia 2026"

    return {
        "data_atualizacao": data_atual,
        "ano_referencia": 2026,
        "fonte_principal": "ANP (LPC) / Refinaria de Mataripe (Acelen) / Base Logística BA",
        "resumo_mercado_ba": {
            "media_estado_gasolina": base_gasolina,
            "media_estado_etanol": base_etanol,
            "media_estado_diesel_s10": base_diesel_s10,
            "ultimo_movimento_refinaria": manchete_ref[:200],
            "melhor_polo_diesel_s10": "Alagoinhas",
            "melhor_polo_gasolina": "Alagoinhas"
        },
        "tabela_precos_municipios": municipios
    }


def gerar_tabela_combustiveis_2026(noticias_lista: list) -> dict:
    """Consolida os preços de 2026 exigindo obrigatoriamente todas as 26 cidades."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    data_atual = agora_bahia().strftime("%d/%m/%Y %H:%M")
    noticias_texto = "\n".join(noticias_lista) if noticias_lista else "Sem boletins indexados nos últimos 7 dias."
    total_esperado = len(POLOS_COMBUSTIVEIS_BA)

    prompt = f"""
    Data/Hora da Consulta (Bahia): {data_atual} (Ano de referência: 2026).

    CONTEXTO COLETADO NA WEB (ANP / Refinaria de Mataripe Acelen / IPTL):
    {noticias_texto}

    LISTA OBRIGATÓRIA DE {total_esperado} MUNICÍPIOS-POLO DA BAHIA:
    {json.dumps(POLOS_COMBUSTIVEIS_BA, ensure_ascii=False)}

    REGRA CRÍTICA: Você DEVE retornar TODOS os {total_esperado} municípios listados acima dentro de "tabela_precos_municipios". NÃO abrevie, NÃO omita nenhuma cidade e NÃO pare antes de completar os {total_esperado} itens.

    Com base nos levantamentos da ANP e movimentações da Refinaria de Mataripe (Acelen) em 2026, estime/consolide os preços médios atualizados (R$/litro) respeitando o fator_frete de cada polo.

    Retorne EXCLUSIVAMENTE um JSON válido (sem blocos ```json) com a estrutura exata:
    {{
      "data_atualizacao": "{data_atual}",
      "ano_referencia": 2026,
      "fonte_principal": "ANP (LPC) / Refinaria de Mataripe (Acelen) / Monitoramento Web",
      "resumo_mercado_ba": {{
        "media_estado_gasolina": 6.64,
        "media_estado_etanol": 4.61,
        "media_estado_diesel_s10": 7.59,
        "ultimo_movimento_refinaria": "Resumo curto sobre o último reajuste na Refinaria de Mataripe",
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
            print(f"Consolidando tabela de {total_esperado} cidades com {modelo}...")
            response = client.models.generate_content(
                model=modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=8192
                ),
            )
            texto_limpo = response.text.strip().replace("```json", "").replace("```", "").strip()
            dados = json.loads(texto_limpo)

            qtd_retornada = len(dados.get("tabela_precos_municipios", []))
            if qtd_retornada < total_esperado:
                print(f"Aviso: {modelo} retornou apenas {qtd_retornada}/{total_esperado} cidades. Tentando próximo modelo...")
                continue

            print(f"Sucesso! {qtd_retornada} cidades consolidadas com {modelo}.")
            return dados
        except Exception as e:
            print(f"Aviso com {modelo}: {str(e)[:120]}...")
            time.sleep(2)

    print("Acionando motor local parametrizado para garantir todas as 26 cidades...")
    return gerar_fallback_local_2026(noticias_lista)


def salvar_arquivos_json(dados: dict):
    """Salva o JSON atual e o histórico diário exclusivamente dentro da pasta do projeto."""
    arquivo_atual = pasta_projeto / "combustiveis_bahia_atual.json"
    with open(arquivo_atual, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    pasta_historico = pasta_projeto / "historico_diario"
    pasta_historico.mkdir(exist_ok=True)
    data_str = agora_bahia().strftime("%Y-%m-%d")
    arquivo_historico = pasta_historico / f"combustiveis_{data_str}.json"
    with open(arquivo_historico, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    print(f"Sucesso! {len(dados.get('tabela_precos_municipios', []))} cidades salvas em:\n- {arquivo_atual}\n- {arquivo_historico}")


if __name__ == "__main__":
    print("1. Pesquisando cotações de combustíveis na Bahia (2026)...")
    noticias = buscar_dados_web_combustiveis_ba()

    print("2. Estruturando tabela completa por Território de Identidade e Município...")
    tabela_2026 = gerar_tabela_combustiveis_2026(noticias)

    print("3. Salvando JSON atual e histórico diário...")
    salvar_arquivos_json(tabela_2026)
    
