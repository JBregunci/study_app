---
title: "Arquitetura web, APIs e REST"
slug: ti-arquitetura-web-apis
summary: "WebSocket, HTTP/2, gRPC, REST, GraphQL e balanceamento."
topics:
  - engenharia-de-software
  - arquitetura-web-apis
tags:
  - es-arquitetura-api
source: "Resumo gerado para o Study App"
source_kind: generated
review_status: approved
---

## Protocolos e APIs

- **HTTP/1.1:** conexões persistentes, mas o tratamento simultâneo de solicitações é limitado.
- **HTTP/2:** multiplexação de várias solicitações em uma conexão, com menor overhead.
- **WebSocket:** comunicação bidirecional sobre uma conexão TCP, usando fluxo de **mensagens**, não de bytes.
- **gRPC:** usa HTTP/2 como transporte e protobuf para serialização.
- **REST:** arquitetura stateless; cada requisição deve conter tudo o que o servidor precisa.
- **GraphQL:** linguagem de consulta para APIs; não executa SQL diretamente no SGBD.

## Balanceamento

No modo ativo-passivo (espera ativa), uma instância reserva assume quando o nó principal falha. Em cluster, um pod é sempre agendado em um nó.

## Como a banca cobra

Inverte HTTP/1 e HTTP/2, chama WebSocket de fluxo de bytes, confunde GraphQL com SQL e troca REST por stateful.

## Checklist rápido

- WebSocket: mensagens.
- HTTP/2: multiplexação.
- gRPC: HTTP/2.
- REST: stateless.
- GraphQL: consulta de API, não SQL direto.
