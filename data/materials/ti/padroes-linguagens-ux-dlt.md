---
title: "Padrões de projeto, linguagens, UX/UI e DLT"
slug: ti-padroes-linguagens-ux-dlt
summary: "GoF, Python/Java, UI/UX, assincronismo e registros distribuídos."
topics:
  - engenharia-de-software
  - padroes-e-linguagens
  - ux-ui
  - dlt-blockchain
tags:
  - es-padroes-linguagens
  - es-ux
  - es-dlt
source: "Resumo gerado para o Study App"
source_kind: generated
review_status: approved
---

## Padrões GoF

- **Criacionais:** abstract factory, builder, factory method, singleton, prototype.
- **Estruturais:** adapter, bridge, composite, decorator, facade, flyweight, proxy.
- **Comportamentais:** observer, strategy, command, state, memento, iterator, entre outros.

Cuidado com descrições trocadas: Facade simplifica uma interface; Builder separa construção e representação. Composite compõe objetos; Decorator adiciona responsabilidades dinamicamente. Memento captura/restaura estado.

## Linguagens e lógica

- Python e Java têm sintaxe e semântica próprias; simule o código antes de concluir o resultado.
- Funções independentes não tornam o código assíncrono; assincronismo exige concorrência explícita (threads, async/await, filas etc.).
- `len` em Python conta caracteres, elementos de lista e chaves de dicionário.

## UX/UI

- **UI design:** aparência, interatividade, sensação visual.
- **UX design:** experiência, interação, estabilidade e facilidade de uso.

## DLT

DLT é uma classe de tecnologias de registro distribuído. Blockchain é um tipo de DLT; DLT não se define apenas como criptografia assimétrica.

## Como a banca cobra

Troca padrões e suas categorias, simula código com resultado incorreto, chama funções síncronas de assíncronas e reduz DLT a criptografia.

## Checklist rápido

- Abstract Factory: criacional.
- Builder: construção/representação.
- Decorator: responsabilidade dinâmica.
- UX/UI: experiência versus aparência.
- DLT ≠ apenas criptografia.
