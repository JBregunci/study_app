# Study App — contexto para agentes

Leia primeiro `docs/PROJECT_STATE.md`. Ele contém o estado vivo do projeto, contagens, pendências e a última sessão.

## Visão geral

Aplicação local de estudos para concursos públicos, em PT-BR, com:

- FastAPI, Jinja2, HTMX e JavaScript vanilla;
- SQLite via SQLAlchemy 2.x;
- questões e materiais em arquivos canônicos;
- tentativas, sessões, conjuntos e estatísticas no SQLite;
- API local em `/api` para futura ingestão por agentes;
- testes com pytest.

## Comandos

```bash
make run       # inicia o servidor local
make test      # roda a suíte
make audit     # auditoria de duplicidades e integridade
make import    # importa catálogo, questões e materiais
```

## Estrutura principal

- `app/`: aplicação, routers, serviços, modelos, templates e estáticos.
- `data/catalog/`: temas, exames e tags controladas.
- `data/questions/`: questões organizadas por exame.
- `data/materials/`: guias em Markdown.
- `data/media/`: imagens usadas pelas questões.
- `data/sources/`: PDFs e textos extraídos; ignorado pelo git.
- `data/backups/`: backups locais do SQLite; ignorado pelo git.
- `docs/`: estado, arquitetura, playbook de ingestão e plano do MCP.
- `tests/`: testes de importação, prática, estatísticas, materiais, API e integridade.

## Regras de dados

- `data/study.db` é o banco local e não deve ser commitado.
- O histórico de sessões/tentativas não pode ser apagado sem pedido explícito do usuário.
- Antes de qualquer mudança de schema, faça backup do banco e prefira migrações aditivas.
- Os JSONs de questões e os Markdown de materiais são a fonte de verdade editorial.
- Questões usam **uma área e um assunto** no catálogo controlado; não crie tags livres ou sinônimos.
- Sempre consulte `data/catalog/tags.json` e `data/catalog/topics.json` antes de classificar algo novo.
- Questões aprovadas de múltipla escolha precisam de justificativa em todas as alternativas; C/E exigem explicação geral.
- O vínculo de material é preciso: tema compatível e, quando o material tiver tags, assunto compartilhado.
- Sugestões de materiais não aparecem durante a resposta; aparecem no resultado e na biblioteca de questões.

## Deduplicação

- `external_id` é a identidade editorial da questão.
- `content_hash` exato evita duplicatas; a política planejada é reutilizar a questão e adicionar vínculo com o novo exame.
- A auditoria procura duplicatas exatas e normalizadas, exames repetidos, tags duplicadas, materiais repetidos e mídias quebradas.
- Não mescle automaticamente questões apenas parecidas; sinalize para revisão.

## Git

- Trabalhe em `main` para este projeto pessoal.
- Use `/checkpoint` ao final de uma sessão para atualizar os docs, rodar testes/auditoria, commitar e fazer push.
- Nunca commite `data/study.db`, `data/sources/`, `data/backups/`, `.venv/` ou segredos.
- O remote é `https://github.com/JBregunci/study_app.git`.

## Ao iniciar uma sessão

1. Ler `docs/PROJECT_STATE.md`.
2. Rodar `git status` e `make test`.
3. Confirmar que o servidor local não está usando um schema antigo.
4. Atualizar `docs/PROJECT_STATE.md` e `docs/SESSION_LOG.md` ao terminar.
