import os
import re
import pandas as pd
from pypdf import PdfReader
from ollama import Client

# Configuração do cliente Ollama
ollama_client = Client(host='http://localhost:11434')

# Dicionário de categorias para palavras-chave 
RULES = {
    "TRANSPORTE": ["posto", "shell", "ipiranga", "uber", "taxi", "táxi", "metrô", "metro", "ônibus", "onibus", "bus", "brt", "99", "cabify"],
    "EDUCACAO":   ["livraria", "cultura", "submarino", "amazon", "udemy", "coursera", "alura", "curso", "escola", "faculdade", "saraiva"],
    "SAUDE":      ["hospital", "clinica", "laboratorio", "laboratório", "drogaria", "farmacia", "farmácia", "ortopedia", "dr. consulta", "drogasil"],
    "LAZER":      ["cinema", "cine", "teatro", "parque", "show", "concert", "museu", "bar", "churrascaria", "bowling"],
    "ALIMENTACAO":["mercado", "padaria", "restaurante", "restaurant", "burger", "lanchonete", "delivery", "food", "pizza", "barbecue", "cafe", "starbucks","boteco"],
    "SERVICOS":   ["netflix", "spotify", "streaming", "assinatura", "serviço", "servico", "subscription", "telefone", "internet", "energia", "água", "oi", "vivo", "claro", "sky"],
    "MERCADO":    ["carrefour", "extra", "oxxo", "pao de açucar", "minuto", "assai", "atacadao", "atacadão", "makro"],
    "VESTUARIO":  ["c&a","riachuelo","renner","zara","h&m","forever 21","marisa","dafiti","nike","adidas","puma","under armour","centauro","track & field","levi’s","lacoste","tommy hilfiger","calvin klein","guess","farm","osklen","hering","animale","amaro","richards"]

}
CATEGORIAS = list(RULES.keys()) + ["OUTROS"]

# Classificação por regra de palavras-chave
def classify_by_rule(descricao: str) -> str:
    tokens = re.findall(r"\w+", descricao.lower())
    for categoria, keywords in RULES.items():
        for kw in keywords:
            if kw in descricao.lower():
                return categoria
    return None

# Classificação via Ollama LLM
def classify_by_llm(descricao: str) -> str:
    regras_text = "\n".join(f"{cat}: {', '.join(words)}" for cat, words in RULES.items())
    prompt = f"""
Você é um classificador de transações baseado em regras.
Para cada descrição abaixo, responda EXATAMENTE com a categoria em MAIÚSCULAS.

Regras de categoria (palavras-chave):
{regras_text}

Transação: "{descricao}"
Resposta:"""
    resp = ollama_client.generate(
        model='llama2:7b-chat-q4_0',
        prompt=prompt
    )['response'].strip()
    # Extrai categoria válida
    m = re.search(r"\b(" + "|".join(CATEGORIAS) + r")\b", resp)
    return m.group(1) if m else None

def classify_transaction(descricao: str) -> str:
    cat = classify_by_rule(descricao)
    if cat:
        return cat
    cat = classify_by_llm(descricao)
    return cat if cat in CATEGORIAS else "OUTROS"

# Funções de extração de texto do PDF

def get_pdf_page_count(reader: PdfReader) -> int:
    return len(reader.pages)

def get_text_pages_brad(reader: PdfReader, i: int) -> str:
    text = reader.pages[i].extract_text() or ""
    if i == 0:
        start, end = "PEDRO HENRIQUE SILVA FARIAS", "Resumo das Despesas"
    else:
        start, end = "Dólar R$", "Total para PEDRO HENRIQUE SILVA FARIAS"
    s, e = text.find(start), text.find(end)
    return text if s < 0 or e < 0 else text[s:e]

# Regex para data, local e valor
pattern_brad = r"(\d{2}/\d{2}) (.+?) (\d+,\d{2})" 

# Ciclo principal
dir_path = r"C:\Users\kraus\Faturas\Faturas Bradesco"
files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.lower().endswith('.pdf')]

transactions = []
termos_excluidos = ["PAGTO ANTECIPADO PIX","PAGTO. POR DEB EM C/C","ENCARGOS DE MORA","ENCARGOS DE MULTA","MULTA CONTRATUAL","ENCARGOS DE ATRASO"]

for path in files:
    reader = PdfReader(path)
    pages = [get_text_pages_brad(reader, i) for i in range(get_pdf_page_count(reader))]
    flat = ' '.join(pages)
    flat = re.sub(r"\s+", ' ', flat)
    for date_str, local, valor_str in geral_pattern.findall(flat):
        if local not in termos_excluidos:
            valor = float(valor_str.replace('.', '').replace(',', '.'))
            cat = classify_transaction(local)
            transactions.append({
                "Data": pd.to_datetime(date_str, format="%d/%m").replace(year=pd.Timestamp.now().year),
                "Local": local.strip(),
                "Valor": valor,
                "Categoria": cat
            })
    print(f"Processado {os.path.basename(path)}; total registros: {len(transactions)}")

# DataFrame final
df = pd.DataFrame(transactions)
print(df)