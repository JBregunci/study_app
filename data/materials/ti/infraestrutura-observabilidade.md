---
title: "Infraestrutura como código e observabilidade"
slug: ti-infraestrutura-observabilidade
summary: "IaC, Docker/Kubernetes, Grafana, Prometheus e APM."
topics:
  - infraestrutura-ti
  - infraestrutura-como-codigo
  - observabilidade
tags:
  - infra-iac
  - infra-observabilidade
source: "Resumo gerado para o Study App"
source_kind: generated
review_status: approved
---

## Infraestrutura como código

IaC define redes, balanceadores, máquinas e outros recursos por código, reduzindo configuração manual e aumentando reprodutibilidade. O manifesto YAML precisa declarar o tipo correto de recurso: `Service` não cria `Deployment`.

## Observabilidade

- **Grafana:** consulta diferentes data sources, transforma dados e monta dashboards.
- **Prometheus:** coleta métricas; **gauge** representa valor que sobe/desce, enquanto **counter** é cumulativo. A descrição de gauge como contador único está errada.
- **APM:** captura traces, latência e taxa de erros, incluindo respostas HTTP 500.
- Observabilidade combina métricas, logs e traces para explicar o comportamento do sistema.

## Como a banca cobra

Troca gauge por counter, confunde Service com Deployment e apresenta APM como se só medisse infraestrutura.

## Checklist rápido

- IaC: recursos por código.
- Grafana: dashboards e múltiplas fontes.
- Gauge: sobe e desce; counter: acumula.
- APM: traces, latência e erros.
