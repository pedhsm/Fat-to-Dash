# Fat to Dash
Organiza Faturas em PDF para Dashboards atráves do uso de AI para organizar e classificar os gastos

## Recursos Destacados
- 🧠 Classificação de transações com Ollama e modelos locais (Mistral/Llama2)
- 📄 Processamento de faturas PDF com extração precisa de texto
- 💾 Armazenamento inteligente em SQLite com histórico mensal
- 🔄 Atualização automática de registros
- 📊 Geração de relatórios em Excel com pandas

## Fluxo de Trabalho
```mermaid
graph TD
    A[PDF da Fatura] --> B{Extrair Texto}
    B --> C[Identificar Transações]
    C --> D[Classificar com IA]
    D --> E[Validar Categoria]
    E --> F[Armazenar no SQLite]
    F --> G[Gerar Relatório Excel]
