# Estado atual do projeto

Última atualização: 2026-11-23

## Resumo

Aplicação funcional local, com banco SQLite, conteúdo do BACEN 2024 (Economia e Finanças e Tecnologia da Informação), 34 materiais e histórico de uso preservado.

## Última sessão

- Checkpoint completo em 2026-11-23: `make test` (42 passando) e `make audit` (sem inconsistências).
- Contagens conferidas contra o SQLite; exames, materiais e tags sem alteração.
- Histórico de uso preservado: 2 sessões e 14 tentativas (inclui simulado aleatório de 10 questões).
- Sem mudança de schema (versão 2) ou de conteúdo editorial nesta sessão.

## Contagens atuais

| Item | Total |
|---|---:|
| Questões | 192 |
| Questões autorais | 12 |
| Questões BACEN Economia e Finanças | 115 |
| Questões BACEN Tecnologia da Informação | 65 específicas + 49 básicas compartilhadas |
| Materiais | 34 |
| Tags controladas | 49 |
| Temas | 78 |
| Exames | 3 |
| Sessões | 2 |
| Tentativas | 14 |
| Conjuntos | 0 |

## Exames importados

| Exame | Cargo | Banca | Ano | Questões |
|---|---|---|---|---:|
| `bacen-2024-analista-economia-financas` | Analista — Economia e Finanças | CEBRASPE | 2024 | 115 (49 básicas + 66 específicas) |
| `bacen-2024-analista-tecnologia-informacao` | Analista — Tecnologia da Informação | CEBRASPE | 2024 | 114 (49 básicas + 65 específicas) |
| `demo-2026` | Analista (demonstração) | DEMO | 2026 | 4 |

As 49 básicas são compartilhadas entre os dois exames BACEN via vínculo muitos-para-muitos; não existem questões duplicadas.

Itens anulados:
- Economia: 44, 52, 64, 83 e 119.
- TI: 53, 55, 56, 61 e 101.

## Trabalho concluído nesta etapa

- BACEN TI importado (65 específicas utilizáveis).
- Básicas compartilhadas entre Economia e TI.
- Filtros por órgão (BACEN) e vínculo múltiplo de exames.
- 9 guias de TI adicionados; cobertura de materiais validada.
- Auditoria `make audit` e política de reutilização de duplicatas.
- Documentos de continuidade e comando `/checkpoint`.
- Plano do MCP em `docs/MCP_INGESTION_PLAN.md`.

## Histórico recente

- Estrutura inicial criada com FastAPI/HTMX/SQLite.
- Banco de questões migrado para catálogo de temas + exames + tags controladas.
- BACEN Economia importado com gabarito oficial conferido.
- Explicações geradas marcadas com selo.
- Materiais passaram a ter múltiplos temas e vínculo preciso; sugestões saíram da tela de resposta.
- Bolinhas das últimas tentativas corrigidas.
- 34 materiais com cobertura de todas as questões.
- BACEN TI importado, com básicas compartilhadas.
- Auditoria e checkpoint adicionados.
- Filtro de concursos reorganizado por órgão/edição, com divisões por cargo, logos e seleção avançada.
- Preservação de espaços e indentação de códigos/YAML nas questões.

## Próximos passos

- Revisar uma amostra das explicações de TI.
- Configurar o MCP do PCI em uma etapa separada.
- Criar fila de revisão de rascunhos.
- Avaliar normalização completa de concurso/cargo se o volume crescer.

## Armadilhas conhecidas

- `data/study.db` está no schema versão 2; rode `make migrate` em bancos antigos.
- `data/study.db` não é versionado; o histórico precisa de migração, não reset.
- Questões básicas podem pertencer a mais de um exame; use `Question.exams`, não duplique.
- PDFs e textos extraídos ficam em `data/sources/`, fora do git.
- Imagens de questões ficam em `data/media/` e precisam de backup.
- O importer deve rejeitar tags fora do catálogo.
- A fonte de verdade editorial são os JSONs/Markdown, não o SQLite.

## Git

- Remote: `https://github.com/JBregunci/study_app.git`
- Branch: `main`, sincronizada com `origin/main`.
- Histórico local e remoto alinhados; use `/checkpoint` para novos envios.
