---
title: "Segurança da Informação, autenticação e NIST"
slug: ti-seguranca-informacao
summary: "SAML, SSO, MFA, ataques web e NIST CSF 2.0."
topics:
  - seguranca-da-informacao
  - autenticacao-e-identidade
  - seguranca-de-aplicacoes
  - nist-csf
tags:
  - si-autenticacao
  - si-aplicacoes
  - si-nist
source: "Resumo gerado para o Study App"
source_kind: generated
review_status: approved
---

## Autenticação e identidade

- **SAML 2.0:** padrão para troca de asserções de autenticação e autorização, muito usado em SSO corporativo. Não é “implementado por OAuth2”; são padrões distintos.
- **OAuth2:** autorização delegada, não autenticação por si só.
- **SSO:** o usuário autentica uma vez e acessa vários serviços. Em SAML, participam o sujeito, o provedor de identidade e o provedor de serviços.
- **MFA:** combina fatores independentes (algo que você sabe, tem ou é).
- **MFA adaptativa:** considera contexto, como localização e tentativas de login.

## Ataques web

- **XSS:** injeção de script; prevenir com validação e sanitização de entradas e escape de saída.
- **Fuzzing:** envia dados aleatórios/malformados em volume para encontrar falhas; não é “poucos dados não aleatórios”.
- **Rate limiting:** controla excesso de requisições e ajuda a evitar respostas 429 por sobrecarga.
- XSS e XXE são ataques, não controles de segurança.

## NIST CSF 2.0

O núcleo tem seis funções: **governar, identificar, proteger, detectar, responder e recuperar**. A versão 2.0 acrescentou a função governar às cinco anteriores.

## Como a banca cobra

Troca SAML por OAuth2, confunde MFA com criptografia de senha, descreve fuzzing incorretamente e reduz o NIST a três funções.

## Checklist rápido

- SAML ≠ OAuth2.
- MFA = fatores independentes, não apenas senha criptografada.
- XSS/XXE são ataques.
- NIST CSF 2.0: seis funções, incluindo governar.
