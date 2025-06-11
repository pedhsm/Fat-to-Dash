import os
import re
import pandas as pd
import matplotlib.pyplot as plt
from pypdf import PdfReader
from ollama import Client

# Configuração do cliente Ollama
ollama_client = Client(host='http://localhost:11434')

# Mapeamento de categorias e regras
RULES = {
    "TRANSPORTE": ["posto","shell","ipiranga","uber","taxi","táxi","metrô","metro","ônibus","onibus","bus","brt","99","cabify"],
    "EDUCACAO":   ["livraria","cultura","submarino","amazon","udemy","coursera","alura","curso","escola","faculdade","saraiva"],
    "SAUDE":      ["hospital","clinica","laboratorio","laboratório","drogaria","farmacia","farmácia","ortopedia","dr. consulta","drogasil"],
    "LAZER":      ["cinema","cine","teatro","parque","show","concert","museu","bar","churrascaria","bowling"],
    "ALIMENTACAO":["mercado","padaria","restaurante","restaurant","burger","lanchonete","delivery","food","pizza","barbecue","cafe","starbucks"],
    "SERVICOS":   ["netflix","spotify","streaming","assinatura","serviço","servico","subscription","telefone","internet","energia","água","oi","vivo","claro","sky"],
    "MERCADO":    ["carrefour","extra","oxxo","pao de açucar","minuto","assai","atacadao","atacadão","makro"],
    "VESTUARIO":  ["c&a","riachuelo","renner","zara","h&m","forever 21","marisa","dafiti","nike","adidas","puma","under armour","centauro","track & field","levi’s","lacoste","tommy hilfiger","calvin klein","guess","farm","osklen","hering","animale","amaro","richards"]
}
CATEGORIAS = list(RULES.keys()) + ["OUTROS"]

# Classificação por regras locais
def classify_by_rule(descricao: str) -> str:
    text = descricao.lower()
    for cat, kws in RULES.items():
        if any(kw in text for kw in kws):
            return cat
    return None

# Classificação via Ollama LLM
def classify_by_llm(descricao: str, candidates=None) -> str:
    cats = candidates if candidates else CATEGORIAS
    regras_block = "\n".join(f"{c}: {', '.join(RULES.get(c, []))}" for c in cats)
    prompt = f"""
Você é um classificador de transações.
Opções: {', '.join(cats)}
Regras:
{regras_block}
Transação: "{descricao}"
Resposta (apenas categoria):"""
    resp = ollama_client.generate(model='llama2:7b-chat-q4_0', prompt=prompt)['response'].strip()
    m = re.search(r"\b(" + "|".join(cats) + r")\b", resp)
    return m.group(1) if m else None

# Função principal de classificação com fallback

def classify_transaction(descricao: str) -> str:
    cat = classify_by_rule(descricao)
    if cat:
        return cat
    cat = classify_by_llm(descricao)
    return cat if cat in CATEGORIAS else "OUTROS"

# Marcação dos termos a excluir
exclude_terms = [
    "PAGTO ANTECIPADO PIX","PAGTO. POR DEB EM C/C",
    "ENCARGOS DE MORA","ENCARGOS DE MULTA","MULTA CONTRATUAL"
]

# Regex para Nubank: data, descrição e valor
pattern_nubank = re.compile(r"(\d{2}\s[A-Z]{3})\s(.+?)\s(-?\d+,\d{2})")

# Processamento da fatura Nubank

dir_path = r"C:\Users\kraus\Faturas\Faturas Nubank"
files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.lower().endswith('.pdf')]
transactions = []

for path in files:
    reader = PdfReader(path)
    # Extrai mês/ano do nome do arquivo
    ym = re.search(r"(\d{4})-(\d{2})", path)
    year, month = (int(ym.group(1)), int(ym.group(2))) if ym else (pd.Timestamp.now().year, None)

    # Extrai transações em bloco por página
    snippets = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ''
        text = ' '.join(text.split())
        # apenas extrai o bloco entre marcadores; caso não ache, pula
        if "TRANSAÇÕES" in text and "PEDRO HENRIQUE SILVA" in text:
            start = text.find("TRANSAÇÕES")
            end = text.find("PEDRO HENRIQUE SILVA")
            snippet = text[start:end]
            snippets.append(snippet)
    flat = ' '.join(snippets)

    # Normaliza espaços e quebra duplicados
    flat = re.sub(r"\s+", ' ', flat)

    # Extrai cada registro
    monthly = []
    for date_str, loc, val_str in pattern_nubank.findall(flat):
        if any(term in loc for term in exclude_terms):
            continue
        # Converte data e valor
        day, mth = date_str.split()
        month_map = {'JAN':1,'FEV':2,'MAR':3,'ABR':4,'MAI':5,'JUN':6,'JUL':7,'AGO':8,'SET':9,'OUT':10,'NOV':11,'DEZ':12}
        dt = pd.Timestamp(year=year, month=month_map.get(mth,1), day=int(day))
        val = float(val_str.replace('.', '').replace(',', '.'))
        cat = classify_transaction(loc)
        monthly.append((dt, loc.strip(), val, cat))
    # Evita duplicação: só adiciona unique
    for rec in monthly:
        if rec not in transactions:
            transactions.append(rec)
    print(f"Processado {os.path.basename(path)}: {len(monthly)} extraídos, {len(transactions)} totais")

# Cria DataFrame e soma
cols = ['Data','Local','Valor','Categoria']
df = pd.DataFrame(transactions, columns=cols)
totals = df.groupby('Categoria')['Valor'].sum()

# Gráfico
totals.plot(kind='bar')
plt.xlabel('Categoria')
plt.ylabel('Total (R$)')
plt.title('Gastos Nubank por Categoria')
plt.tight_layout()
plt.show()
