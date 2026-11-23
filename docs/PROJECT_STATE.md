# Estado atual do projeto

Última atualização: 2026-11-23

## Resumo

Aplicação funcional local, com banco SQLite, conteúdo do BACEN 2024 (Economia e Finanças), 25 materiais e histórico de uso preservado.

## Contagens atuais

| Item | Total |
|---|---:|
| Questões | 127 |
| Questões autorais | 12 |
| Questões BACEN Economia e Finanças | 115 |
| Materiais | 25 |
| Tags controladas | 26 |
| Temas | 49 |
| Sessões | 1 |
| Tentativas | 4 |
| Conjuntos | 0 |

## Exames importados

| Exame | Cargo | Banca | Ano | Questões |
|---|---|---|---|---:|
| `bacen-2024-analista-economia-financas` | Analista — Economia e Finanças | CEBRASPE | 2024 | 115 |
| `demo-2026` | Analista (demonstração) | DEMO | 2026 | 4 |

Os itens anulados do BACEN Economia são 44, 52, 64, 83 e 119. Eles não entram na prática.

## Trabalho em andamento

- Importar o BACEN 2024 — Analista de Tecnologia da Informação (65 questões utilizáveis).
- Compartilhar as 49 básicas com os exames de Economia e TI via vínculo muitos-para-muitos.
- Adicionar filtros por órgão/edição (BACEN 2024).
- Adicionar 8–10 guias de TI.
- Criar auditoria `make audit` e política de reutilização de duplicatas.
- Criar documentos de continuidade/checkpoint.
- Salvar o plano do MCP em `docs/MCP_INGESTION_PLAN.md`.

## Histórico recente

- Estrutura inicial criada com FastAPI/HTMX/SQLite.
- Banco de questões migrado para catálogo de temas + exames + tags controladas.
- BACEN Economia importado com gabarito oficial conferido.
- Explicações geradas marcadas com selo.
- Materiais passaram a ter múltiplos temas e vínculo preciso; sugestões saíram da tela de resposta.
- Bolinhas das últimas tentativas corrigidas.
- 25 materiais com cobertura de todas as questões.

## Próximos passos após a etapa atual

- Validar filtros por BACEN e por edição.
- Revisar materiais de TI e cobertura.
- Configurar o MCP do PCI em uma etapa separada.
- Criar fila de revisão de rascunhos.
- Avaliar normalização completa de concurso/cargo se o volume crescer.

## Armadilhas conhecidas

- `data/study.db` não é versionado; o histórico precisa de migração, não reset.
- PDFs e textos extraídos ficam em `data/sources/`, fora do git.
- Imagens de questões ficam em `data/media/` e precisam de backup.
- O importer deve rejeitar tags fora do catálogo.
- A fonte de verdade editorial são os JSONs/Markdown, não o SQLite.
