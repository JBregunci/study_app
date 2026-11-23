---
title: "Ciência de Dados, Machine Learning e IA"
slug: ti-ciencia-de-dados-ia
summary: "ML, Big Data, LLMs, MLOps, qualidade e ética em IA."
topics:
  - ciencia-de-dados
  - machine-learning
  - big-data
  - llm-ia-generativa
  - mlops
  - qualidade-e-etica-ia
tags:
  - cd-ml
  - cd-bigdata
  - cd-llm
  - cd-mlops
  - cd-qualidade-etica
source: "Resumo gerado para o Study App"
source_kind: generated
review_status: approved
---

## Machine Learning

- **Supervisionado:** usa rótulos; exemplos: classificação e regressão.
- **Não supervisionado:** busca estrutura sem rótulos; agrupamento e associação.
- **Transfer learning:** reutiliza conhecimento entre domínios/tarefas. Na forma transdutiva, a tarefa é a mesma e o domínio muda; na indutiva, a tarefa muda.
- **Validação cruzada:** avalia generalização e ajuda a detectar overfitting/underfitting.
- **K-fold:** divide em k partes; k−1 para treino e 1 para validação/teste, repetindo k vezes.

## Big Data e NLP

- BoW transforma texto em vetor de frequências, mas perde ordem e contexto.
- Deep learning reduz parte do pré-processamento, mas não elimina automaticamente todos os cuidados.
- LLMs usam tokens e parâmetros como **temperature** para controlar aleatoriedade/diversidade.

## MLOps e qualidade

- MLOps cobre ingestão, preparação, treino, validação, implantação e monitoramento.
- Versionamento de dados, código e modelos garante reprodutibilidade e auditoria.
- Qualidade de dados inclui consistência, completude, acurácia e validade.
- Ética em IA valoriza transparência, explicabilidade, privacidade e responsabilização; opacidade não é padrão recomendado.

## Como a banca cobra

Troca aprendizado supervisionado por não supervisionado, inverte K-fold, afirma que BoW preserva contexto, confunde thread com assistente em LLM e exagera o papel da opacidade.

## Checklist rápido

- BoW: frequência, sem ordem/contexto.
- K-fold: treino com k−1, validação com 1.
- Transdutiva: mesma tarefa, domínio diferente.
- Temperature: maior = mais diversidade.
- Governança de IA: transparência, não opacidade.
