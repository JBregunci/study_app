---
title: "DevOps, DevSecOps e testes de software"
slug: ti-devops-testes
summary: "CI/CD, DAST, BDD, TDD e desenvolvimento seguro."
topics:
  - engenharia-de-software
  - devops-testes
tags:
  - es-devops-testes
source: "Resumo gerado para o Study App"
source_kind: generated
review_status: approved
---

## DevOps e DevSecOps

DevOps combina cultura, colaboração, automação, medição e compartilhamento para encurtar o ciclo de entrega. CI/CD automatiza integração, testes e entrega. DevSecOps incorpora segurança ao longo de todo o ciclo, com análise estática, dinâmica e de dependências.

- **SAST:** análise estática do código.
- **DAST:** teste dinâmico da aplicação em execução, alinhado a recomendações OWASP.
- **SCA:** análise de dependências e bibliotecas.

## Testes

- **TDD:** o teste é escrito antes do código (red-green-refactor).
- **BDD:** usa linguagem de negócio e histórias de usuário; nomes de testes podem ser frases compreensíveis.
- **Testes unitários:** isolam unidades; **integração:** combinam componentes; **ponta a ponta:** exercitam o fluxo completo.

## Desenvolvimento seguro

- Validar e sanitizar entradas.
- Evitar exposição de erros internos.
- Aplicar rate limiting contra abuso.
- Prevenir XSS e XXE com escape, validação e configuração segura de parsers.

XSS e XXE são ataques; não são “boas práticas” em si. Código independente não é automaticamente assíncrono; é preciso concorrência explícita.

## Como a banca cobra

Troca a ordem do TDD, confunde DAST com SAST e apresenta ataques como controles.

## Checklist rápido

- TDD: teste antes.
- BDD: linguagem de negócio.
- DAST: aplicação em execução.
- DevSecOps: segurança em todo o ciclo.
