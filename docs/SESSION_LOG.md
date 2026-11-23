# SESSION_LOG

## 2026-11-23 — Base do Study App

- Criada aplicação FastAPI + HTMX + SQLite.
- Implementadas prática sequencial, simulado aleatório, timer, feedback, estatísticas e conjuntos.
- Criado banco de questões autoral e importador JSON.
- Criada API local de consulta/importação.

## 2026-11-23 — BACEN Economia e Finanças

- Importadas 115 questões utilizáveis do BACEN 2024 — Analista Economia e Finanças.
- Anuladas excluídas: 44, 52, 64, 83 e 119.
- Gabarito oficial definitivo conferido para todas as questões.
- Imagens dos gráficos e do jogo extraídas.
- Explicações geradas com selo.
- Criados 25 materiais.

## 2026-11-23 — Taxonomia e vínculos

- Substituídas 102 tags granulares por 26 assuntos amplos com área.
- Uma tag de assunto por questão.
- Materiais passaram a apontar para múltiplos temas e a usar vínculo preciso.
- Sugestões de material removidas da tela de resposta; exibidas no resultado e na biblioteca.
- Corrigidas as bolinhas das últimas 5 tentativas.
- Adicionadas estatísticas por área e assunto.
- Reset do histórico anterior autorizado pelo usuário.

## 2026-11-23 — BACEN TI e continuidade

- Localizada e importada a prova oficial do BACEN TI (65 específicas utilizáveis).
- Básicas compartilhadas entre Economia e TI via vínculo M2M.
- Adicionados órgão/edição aos exames e filtro por BACEN.
- Adicionados 9 materiais de TI; cobertura total validada.
- Implementados `make audit` e política de reutilização de duplicatas.
- Criados AGENTS.md, PROJECT_STATE, SESSION_LOG, ARCHITECTURE, INGESTION_PLAYBOOK, MCP plan e `/checkpoint`.
- Criado `scripts/migrate_schema.py` (schema versão 2).
- Histórico de 1 sessão/4 tentativas preservado.
- Commit de baseline criado localmente; push pendente por ausência de credenciais do GitHub no ambiente.

## 2026-11-23 — Ajustes de filtro e código

- Filtro de concursos agrupado por órgão/edição, com divisões por cargo, logos e seleção avançada.
- Corrigida a renderização de YAML/código preservando espaços e indentação.
- Testes atualizados; 42 passando.

## 2026-11-23 — Checkpoint

- `make test`: 42 testes passando; `make audit`: sem duplicidades ou inconsistências.
- Contagens conferidas: 192 questões, 34 materiais, 49 tags, 3 exames.
- Histórico preservado: 2 sessões e 14 tentativas (simulado aleatório de 10 questões).
- Sem mudanças de schema ou de conteúdo editorial.
