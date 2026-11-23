# Playbook de ingestão

## Antes de começar

1. Leia `docs/PROJECT_STATE.md`.
2. Faça backup de `data/study.db` em `data/backups/`.
3. Confira `data/catalog/topics.json`, `exams.json` e `tags.json`.
4. Nunca crie tag nova sem verificar se já existe um assunto equivalente.

## Adicionar um concurso

1. Localize a prova e o gabarito oficial da banca.
2. Preencha `data/catalog/exams.json`:
   - órgão;
   - banca;
   - ano;
   - cargo/área;
   - edital;
   - URLs da prova e do gabarito.
3. Use uma chave estável de edição (`contest_key`) para agrupar cargos do mesmo concurso.
4. Se o mesmo concurso já existe, atualize em vez de criar outro.

## Adicionar temas e assuntos

- Temas vão em `topics.json`, preferencialmente em uma árvore.
- Assuntos vão em `tags.json`, com `area` ampla e nome único.
- Antes de criar um assunto, procure sinônimos e tags existentes.
- Uma questão deve apontar para um único assunto.
- Conceitos muito específicos ficam no tema ou na explicação, não em uma tag nova.

## Adicionar questões

1. Extraia o texto do PDF e o gabarito oficial.
2. Exclua itens anulados ou marque-os para não entrar na prática.
3. Preserve contexto compartilhado, código, tabelas e imagens.
4. Use IDs estáveis: `<orgao>-<ano>-<cargo>-qNNN`.
5. Preencha:
   - `external_id`, `exam`, `topic`, `tag`;
   - `type`, `statement`, `context`;
   - `source`, `source_url`, `source_question_number`;
   - `origin: official`, `answer_source: official_key`, `explanation_source: generated`;
   - `review_status: approved` somente após validação;
   - explicação geral;
   - alternativas C/E ou A–E.
6. Rode a importação e confira o relatório.
7. Rode `make audit`.

## Duplicatas

- Mesmo `external_id`: atualização.
- Mesmo conteúdo exato: reutilizar a questão e adicionar vínculo com o novo exame.
- Conteúdo quase igual: sinalizar para revisão; não mesclar automaticamente.
- Concurso repetido: upsert pela chave normalizada de órgão/banca/ano/cargo/edital.

## Materiais

1. Crie um guia curto por área/assunto, não por questão.
2. Use frontmatter com `topics` e `tags`.
3. O guia deve explicar o que a questão cobra, com conceitos, pegadinhas e checklist.
4. Garanta que toda questão tenha pelo menos um material relacionado.
5. Rode a cobertura no audit.

## Explicações geradas

- Marque `explanation_source: generated`.
- Confira o gabarito oficial.
- Se houver dúvida, deixe `review_status: draft` e sinalize.
- Nunca apresente explicação gerada como comentário oficial.

## Verificação final

```bash
make import
make test
make audit
```

Depois, use `/checkpoint` para atualizar `PROJECT_STATE.md`, `SESSION_LOG.md`, commitar e fazer push.
