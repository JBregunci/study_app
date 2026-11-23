# Estudo para Concursos

Aplicação web local para estudar para concursos públicos com questões reais e autorais. Roda no navegador, usa Python no backend e guarda o histórico no seu computador.

## Funcionalidades

- Banco de questões com filtros por tema hierárquico, concurso, banca, ano, cargo, formato, dificuldade, tag e situação.
- Histórico visual das últimas 5 tentativas de cada questão, com bolinhas de acerto/erro e espaços para tentativas ausentes.
- Prática sequencial por tema, incluindo subtemas, com retomada de sessões em andamento.
- Simulados aleatórios de 10 a 20 questões, filtrando por tema e concurso.
- Timer por questão controlado no servidor, com limite opcional.
- Correção imediata ou ao final da sessão.
- Feedback com destaque da alternativa correta, da escolha errada e justificativas.
- Resultado com melhor tema, tema a reforçar e tabela de desempenho por tema.
- Retentativa de uma questão específica, com feedback imediato.
- Erros recentes agrupados por questão, com status “Refeita e acertada”, “Refeita, ainda incorreta” ou “Não refeita”.
- Seção de materiais expositivos em Markdown, ligados a temas, tags e questões.
- Estatísticas diárias, sequência de estudo, gráfico dos últimos dias e revisão de erros.
- Conjuntos personalizados de questões para um concurso ou cargo.
- Tema claro/escuro.
- API local para consulta e ingestão futura por agentes.
- Importação automática de catálogo, questões e materiais ao iniciar.

## Conteúdo atual

- 12 questões autorais de demonstração.
- **180 questões reais do BACEN 2024**: 115 de Analista — Economia e Finanças e 65 específicas de Analista — Tecnologia da Informação.
- As 49 questões básicas são **compartilhadas** entre os dois cargos, sem duplicação.
- **34 guias de material**, ligados a temas, áreas, assuntos e questões.
- Anuladas não entram na prática: Economia (44, 52, 64, 83, 119) e TI (53, 55, 56, 61, 101).
- As explicações das questões reais são geradas e marcadas com o selo **“Explicação gerada”**. O gabarito usado é o oficial definitivo do CEBRASPE.
- Toda questão do banco tem um assunto amplo, uma área e pelo menos um material relevante.
- Total atual: **192 questões** (12 autorais + 180 do BACEN), **49 assuntos** e **3 exames cadastrados**.

Fontes oficiais:

- Conhecimentos básicos: `https://cdn.cebraspe.org.br/concursos/bcb_24/arquivos/959_BCB_CB1_01.PDF`
- Gabarito básico: `https://cdn.cebraspe.org.br/concursos/bcb_24/arquivos/GAB_DEFINITIVO_959_BCB_CB1_01.PDF`
- Economia e Finanças: `https://cdn.cebraspe.org.br/concursos/bcb_24/arquivos/959_BCB_001_01.PDF`
- Gabarito Economia: `https://cdn.cebraspe.org.br/concursos/bcb_24/arquivos/GAB_DEFINITIVO_959_BCB_001_01.PDF`
- Tecnologia da Informação: `https://cdn.cebraspe.org.br/concursos/bcb_24/arquivos/959_BCB_002_01.PDF`
- Gabarito TI: `https://cdn.cebraspe.org.br/concursos/bcb_24/arquivos/GAB_DEFINITIVO_959_BCB_002_01.PDF`

## Requisitos

- Python 3.11 ou superior (testado com 3.13).
- SQLite, já incluído no Python.
- Nenhum Node.js ou passo de build.

## Como rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Ou:

```bash
make setup
make run
```

Abra `http://127.0.0.1:8000`.

O SQLite fica em `data/study.db`. Na primeira execução, o catálogo, as questões e os materiais são importados automaticamente. As execuções seguintes atualizam o conteúdo de forma idempotente. Se o banco vier de uma versão anterior com schema antigo, rode `make migrate` antes de iniciar.

## Estrutura

```text
app/
  main.py                 aplicação FastAPI
  models.py               modelos SQLAlchemy
  schemas.py              validação dos JSONs e frontmatter
  routers/                painel, questões, concursos, temas, prática, conjuntos, materiais, estatísticas e API
  services/               importação, auditoria, prática, estatísticas, banco de questões e taxonomia
  templates/              páginas Jinja2
  static/                 CSS, JavaScript, HTMX e favicon
data/
  catalog/
    topics.json           árvore de temas e subtemas
    exams.json            concursos, cargos, bancas, anos e fontes
    tags.json             áreas e assuntos controlados
  questions/
    sample/               questões autorais
    bacen-2024/           questões reais do BACEN
  materials/              guias em Markdown
  media/                  imagens usadas pelas questões
  sources/                PDFs oficiais, fora do git
  study.db                banco local, fora do git
scripts/
  import_questions.py     importação manual
  audit_library.py        auditoria de duplicidades
  migrate_schema.py       migrações aditivas
docs/                     estado, arquitetura, playbook, MCP e histórico
.opencode/command/        comando /checkpoint
tests/                    testes com pytest
```

## Onde cada dado fica

- **Catálogo:** `data/catalog/topics.json`, `data/catalog/exams.json` e `data/catalog/tags.json`.
- **Questões:** arquivos JSON em `data/questions/`, com o conteúdo importado para o SQLite.
- **Materiais:** arquivos Markdown em `data/materials/`, também importados para o SQLite.
- **Sessões, respostas, conjuntos e desempenho:** somente no SQLite `data/study.db`.
- **Mídias de questões:** `data/media/`, servidas em `/media/...`.
- **PDFs oficiais:** `data/sources/`, ignorados pelo git.
- **Backup:** copie `data/study.db`, `data/questions/`, `data/materials/` e `data/media/`.

## Catálogo de temas, assuntos e concursos

Os temas formam uma árvore. Uma questão aponta para o tema folha, mas filtros por um tema pai incluem automaticamente todos os descendentes.

As tags são controladas por `tags.json` e funcionam como **assuntos amplos**, agrupados por **área** (Língua Portuguesa, Estatística, Direito, Economia, Microeconomia, Finanças, Contabilidade, Raciocínio Lógico, Informática e Sistema Financeiro). Cada questão tem **um único assunto**. Conceitos muito específicos ficam no subtema e na explicação, evitando dezenas de tags duplicadas.

Exemplo de `topics.json`:

```json
{
  "topics": [
    {"slug": "economia", "name": "Economia", "position": 80},
    {"slug": "macroeconomia", "name": "Macroeconomia", "parent": "economia", "position": 81},
    {"slug": "politica-monetaria", "name": "Política Monetária", "parent": "macroeconomia", "position": 83}
  ]
}
```

Exemplo de `exams.json`:

```json
{
  "exams": [
    {
      "slug": "bacen-2024-analista-economia-financas",
      "name": "Banco Central do Brasil (BACEN)",
      "organization": "CEBRASPE",
      "year": 2024,
      "role": "Analista — Área: Economia e Finanças",
      "edital": "Edital 8/2024",
      "source_url": "https://cdn.cebraspe.org.br/...",
      "answer_key_url": "https://cdn.cebraspe.org.br/..."
    }
  ]
}
```

O ano, a banca e o cargo ficam no catálogo do concurso e aparecem em cada questão. Assim evitamos duplicar metadados e mantemos os filtros consistentes.

## Formato das questões

Um arquivo de questões contém apenas a lista `questions`; temas e concursos já vêm do catálogo.

```json
{
  "questions": [
    {
      "external_id": "bacen-2024-analista-economia-financas-q047",
      "topic": "politica-monetaria",
      "exam": "bacen-2024-analista-economia-financas",
      "type": "true_false",
      "difficulty": "medio",
      "source_question_number": "47",
      "context": "Texto ou situação compartilhada pelos itens 46 a 50.",
      "statement": "Quando o BCB define a taxa Selic, ...",
      "origin": "official",
      "answer_source": "official_key",
      "explanation_source": "generated",
      "review_status": "approved",
      "source": "CEBRASPE — BCB — Edital 8/2024",
      "source_url": "https://cdn.cebraspe.org.br/...",
      "tag": "macro-politica-monetaria",
      "general_explanation": "O item está errado porque ...",
      "alternatives": [
        {"label": "C", "text": "Certo", "is_correct": false},
        {"label": "E", "text": "Errado", "is_correct": true}
      ]
    }
  ]
}
```

Regras principais:

- `type`: `single_choice` (A–E) ou `true_false` (C/E).
- Exatamente uma alternativa correta.
- Questões aprovadas de múltipla escolha exigem explicação em todas as alternativas.
- Questões C/E exigem explicação geral; explicação por alternativa é opcional.
- `tag`: slug do assunto no catálogo controlado; cada questão tem exatamente um.
- `origin`: `official`, `derived` ou `authored`.
- `answer_source`: `official_key`, `manual` ou `generated`.
- `explanation_source`: `official`, `manual` ou `generated`.
- `review_status`: `draft`, `approved` ou `archived`.
- `context` e `context_media_url` guardam textos, tabelas e figuras compartilhados por vários itens.
- `content_hash` é calculado na importação para evitar duplicatas.

## Importação

Automática ao iniciar. Para rodar manualmente:

```bash
make import
```

Ou:

```bash
.venv/bin/python -m scripts.import_questions
.venv/bin/python -m scripts.import_questions data/questions/bacen-2024/lote-01-basicos.json
.venv/bin/python -m scripts.import_questions data/questions --status draft
```

O comando importa catálogo, questões e materiais quando o caminho é um diretório, e mostra criadas, atualizadas, reutilizadas, ignoradas e erros. Duplicatas exatas são reaproveitadas com vínculo ao novo exame. Um arquivo inválido não derruba a aplicação.

## Página Questões

- Filtro principal por **concurso**, agrupado por órgão/edição e com as divisões por cargo; cada organização tem um logo no seletor.
- **Seleção avançada** para banca, ano, formato, dificuldade, área e assunto.
- Filtros por busca, tema, situação e ordenação no fluxo principal.
- Paginação e ordenação por mais recentes, mais erradas ou menos praticadas.
- Bolinhas com as últimas 5 tentativas: verde para acerto, vermelho para erro ou branco, transparente para tentativa ausente.
- Página de detalhe com contexto, enunciado, gabarito comentado, fonte, tags, histórico de tentativas e materiais relacionados.
- Botão **Refazer** em qualquer questão aprovada.

## Retentativas e erros recentes

- O botão **Tentar novamente** cria uma sessão de uma questão, com correção imediata.
- A nova tentativa entra normalmente nas estatísticas.
- “Erros recentes” é agrupado por questão e mostra o último erro.
- Se houver tentativa posterior correta, o erro recebe o selo **Refeita e acertada**.
- Se a tentativa posterior continuar errada, recebe **Refeita, ainda incorreta**.
- É possível ocultar ou mostrar erros resolvidos.

## Resultado da sessão

- Aproveitamento, acertos, erros, brancos e tempo total.
- Melhor tema e tema a reforçar naquela sessão.
- Tabela por tema com feitas, acertos, erros/brancos, aproveitamento e links para questões e materiais.
- Resumo por formato C/E e múltipla escolha.
- **Materiais para reforçar**, sugeridos apenas depois do término da sessão.
- Revisão completa das questões e botão de retentativa nas erradas.

A página de estatísticas inclui **desempenho por área** e **desempenho por assunto**, além do desempenho por tema/subtema.

## Materiais expositivos

Os materiais são arquivos Markdown com frontmatter:

```markdown
---
title: "Política Monetária e Selic"
slug: politica-monetaria
summary: "Resumo curto para revisão."
topics:
  - macroeconomia
  - politica-monetaria
tags:
  - macro-politica-monetaria
source: "Resumo gerado para o Study App"
source_kind: generated
review_status: approved
---

## Visão geral

Conteúdo do guia.
```

- A seção `/materiais` permite busca e filtros por tema/tag.
- O guia mostra questões relacionadas por temas e assuntos, com as mesmas bolinhas de desempenho.
- Os materiais aparecem no **resultado da sessão** e na **biblioteca de questões**, nunca durante a resposta de uma questão.
- O vínculo exige tema compatível e, quando houver, assunto compartilhado; isso evita sugestões desconexas.
- O conteúdo é renderizado com sanitização.

## API para agentes

A API fica em `http://127.0.0.1:8000/api` e usa o mesmo schema JSON de questões.

| Método | Rota | Uso |
|---|---|---|
| `GET` | `/api/health` | Status da aplicação |
| `GET` | `/api/questions` | Lista questões; aceita `topic`, `exam`, `status`, `limit`, `offset` |
| `GET` | `/api/questions/{external_id}` | Consulta uma questão pelo ID externo |
| `POST` | `/api/questions/import` | Importa questões; padrão `draft` |

A importação via API grava como `draft` por padrão. Para aprovar, envie `review_status: "approved"` com as explicações necessárias. Ainda não existe tela de revisão de rascunhos.

Exemplo:

```bash
curl -X POST http://127.0.0.1:8000/api/questions/import \
  -H "Content-Type: application/json" \
  --data @questoes.json
```

## Continuidade e checkpoint

- `AGENTS.md` é o ponto de entrada para novos agentes.
- `docs/PROJECT_STATE.md` guarda o estado vivo, contagens, exames e pendências.
- `docs/SESSION_LOG.md` registra o que foi feito em cada sessão.
- `docs/ARCHITECTURE.md`, `docs/INGESTION_PLAYBOOK.md` e `docs/MCP_INGESTION_PLAN.md` documentam arquitetura, ingestão e o plano do MCP.
- `/checkpoint` atualiza docs, roda testes/auditoria, commita e faz push.

## Ideias para popular novos concursos

1. Catalogar o concurso e o cargo em `data/catalog/exams.json`.
2. Baixar prova e gabarito oficiais da banca.
3. Extrair o texto e os itens com um script auxiliar, preservando contextos, tabelas e figuras.
4. Classificar cada item na árvore de temas e escolher um assunto do catálogo de tags.
5. Gerar explicações alinhadas ao gabarito oficial.
6. Importar como rascunho e revisar uma amostra antes de liberar.
7. Marcar itens anulados para não entrarem na prática.

Para gerar variantes C/E de questões A-E no futuro:

- Não transformar alternativas mecanicamente.
- Criar itens derivados com contexto próprio, `origin: "derived"`, vínculo com a questão original e status rascunho.
- Manter esses itens separados dos oficiais e revisar antes de aprovar.

## Testes

```bash
make test
make audit
```

A suíte cobre importação, catálogo, áreas/assuntos, questões C/E e A-E, privacidade das explicações no modo ao final, timeout, filtros, últimas tentativas, retentativas, erros resolvidos, materiais, vínculos precisos, cobertura de materiais, gabarito oficial do BACEN, sanitização e API.

## Configuração opcional

Variáveis de ambiente:

| Variável | Padrão | Descrição |
|---|---|---|
| `STUDY_DB_PATH` | `data/study.db` | Caminho do banco SQLite |
| `STUDY_TIMEZONE` | `America/Sao_Paulo` | Fuso das datas diárias |
| `STUDY_AUTO_IMPORT` | `1` | Defina `0` para desativar a importação no startup |

## Limitações atuais

- Aplicação para um único usuário local, sem login.
- Sem cronômetro total de prova; existe limite opcional por questão.
- Sem questões com múltiplas respostas corretas.
- Sem editor de questões ou materiais pelo navegador; a autoria é feita nos arquivos JSON/Markdown.
- Sem tela de revisão de rascunhos.
- As explicações das questões reais são geradas e devem ser conferidas com o gabarito oficial.
- O plano do MCP está documentado, mas o servidor ainda não foi configurado.
