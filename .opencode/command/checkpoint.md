---
description: Atualiza docs, roda testes/auditoria, commita e faz push do progresso.
agent: build
---

Faça um checkpoint completo deste projeto.

Passos obrigatórios:

1. Leia `AGENTS.md`, `docs/PROJECT_STATE.md` e `docs/SESSION_LOG.md`.
2. Rode `make test`.
3. Rode `make audit`.
4. Atualize `docs/PROJECT_STATE.md`:
   - contagens atuais;
   - exames importados;
   - pendências;
   - última sessão;
   - mudanças de schema ou dados relevantes.
5. Acrescente uma entrada curta em `docs/SESSION_LOG.md` com a data e o que foi feito.
6. Revise `git status` e `git diff`.
7. Faça stage apenas de arquivos intencionais. Nunca inclua:
   - `data/study.db`
   - `data/sources/`
   - `data/backups/`
   - `.venv/`
   - segredos
8. Faça commit com uma mensagem descritiva, em português.
9. Faça push para `origin main`.
10. Se o push falhar, mantenha o commit local e informe o erro com os passos necessários.

Não faça commit se os testes ou a auditoria falharem. Corrija primeiro ou relate o bloqueio.
