---
title: "Bancos de dados, agilidade e governança de TI"
slug: ti-bancos-gestao
summary: "SQL, 3FN, sharding, data warehouse, Scrum, Kanban, governança e ITIL."
topics:
  - bancos-de-dados
  - modelagem-sql
  - nosql-data-warehouse
  - gestao-ti
  - agil-scrum-kanban
  - governanca-dados-itil
tags:
  - bd-sql
  - bd-nosql-dw
  - gestao-agil
  - gestao-governanca-itil
source: "Resumo gerado para o Study App"
source_kind: generated
review_status: approved
---

## Bancos de dados

- **SELECT:** pode conter várias subqueries internas.
- **3FN:** elimina dependências transitivas. Dependências multivaloradas são tratadas na 4FN.
- **Sharding:** distribui dados entre nós para escalabilidade e balanceamento de carga.
- **Data warehouse:** projetado para análise; deadlocks dependem de concorrência e bloqueios, não apenas do volume de dados.

## Scrum e Kanban

- O **product owner** prioriza o product backlog e maximiza valor. O time de desenvolvimento decide como executar o trabalho.
- **Kanban** visualiza o fluxo e o progresso; pode ser usado junto ao Scrum para dar visibilidade.

## Governança de dados e ITIL

- Governança de dados inclui planejamento, definição de estratégia, políticas, papéis e monitoramento.
- ITIL v4 trata o gerenciamento de risco como prática para identificar, avaliar e tratar riscos, inclusive os que afetam níveis de serviço.

## Como a banca cobra

Define 3FN como multivalorada, atribui ao product owner o “como” da execução e confunde riscos de volume com deadlocks.

## Checklist rápido

- 3FN: dependência transitiva; 4FN: multivalorada.
- Sharding: distribuição/balanceamento.
- Product owner: o quê/prioridade; time: como.
- Kanban: fluxo visual.
