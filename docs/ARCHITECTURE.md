# Arquitetura

## Stack

- FastAPI para rotas HTTP e API.
- Jinja2 para templates server-side.
- HTMX para respostas parciais; JavaScript vanilla para timer, tema e filtros.
- SQLite + SQLAlchemy 2.x.
- Conteúdo editorial em JSON/Markdown; SQLite guarda o runtime e o histórico.
- pytest + httpx para testes.

## Módulos

```text
app/
  main.py          criação da app, startup, imports automáticos
  models.py        modelos SQLAlchemy
  schemas.py       validação Pydantic de JSON e frontmatter
  routers/         painel, questões, concursos, temas, prática, conjuntos, materiais, estatísticas, API
  services/        importação, prática, estatísticas, banco de questões, taxonomia e materiais
  templates/       páginas Jinja2 e parciais HTMX
  static/          CSS, JS, HTMX e favicon
```

## Dados

### Catálogo

- `data/catalog/topics.json`: árvore de temas.
- `data/catalog/exams.json`: concursos/cargos, banca, órgão, chave de edição, ano, edital e fontes.
- `data/catalog/tags.json`: assuntos amplos agrupados por área.

### Questões

- `data/questions/**/*.json`: fonte de verdade editorial.
- Importador faz upsert por `external_id`, calcula `content_hash` e valida tags/temas.
- Questões têm contexto opcional, mídia, proveniência, gabarito, explicação e alternativas.
- Uma questão pode pertencer a vários exames (`question_exams`); básicas são compartilhadas sem duplicação.
- C/E têm exatamente duas alternativas (C/E); múltipla escolha usa A–E.

### Materiais

- `data/materials/**/*.md`: Markdown com frontmatter.
- Cada material aponta para um ou mais temas e para assuntos controlados.
- O vínculo com questão exige tema compatível e, se o material tiver tags, tag compartilhada.

### Runtime

- `data/study.db`: SQLite local, não versionado.
- Sessões, itens de sessão, tentativas, conjuntos e histórico ficam fora do git.
- `data/media/`: imagens editoriais versionadas.
- `data/sources/`: PDFs e textos extraídos, fora do git.

## Fluxo de prática

1. Sessão é criada com itens ordenados.
2. Cada item recebe `shown_at` ao ser exibido.
3. Resposta é validada no servidor e grava tentativa única por sessão/questão.
4. Timer e timeout são calculados no servidor a partir de `shown_at`.
5. Resultado agrega tema, tipo, melhor/pior desempenho e materiais.
6. Retentativa cria uma nova sessão de uma questão; resolução é inferida por tentativa posterior.

## Deduplicação

- `external_id` é a identidade editorial.
- `content_hash` exato é único no banco.
- A política implementada reutiliza a questão existente e cria vínculo com um novo exame em vez de duplicar.
- Quase duplicatas normalizadas são sinalizadas para revisão.
- `make audit` verifica questões, exames, tags, materiais e mídias.

## Decisões de produto

- Interface PT-BR, dados locais, sem login.
- Um assunto amplo por questão; detalhes ficam nos temas e na explicação.
- Materiais não aparecem durante a resposta; aparecem no resultado e na biblioteca.
- Explicações geradas são identificadas com selo.
- Anuladas não entram na prática.
