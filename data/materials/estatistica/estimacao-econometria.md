---
review_status: approved
slug: estatistica-estimacao-econometria
source: Resumo gerado para o Study App
source_kind: generated
summary: Método dos momentos, máxima verossimilhança, estacionariedade e dados em
  painel.
tags:
- estatistica-inferencia-econometria
title: Estimação, séries temporais e econometria
topics:
- estatistica
- inferencia-estatistica
- series-temporais
- dados-em-painel
- processos-estocasticos
---

## Método dos momentos

O método dos momentos iguala momentos populacionais aos momentos amostrais. Para uma distribuição de Poisson, E[X] = λ. Se a média amostral é 1,6, a estimativa de λ por momentos também é 1,6.

## Máxima verossimilhança

A estimativa de máxima verossimilhança maximiza a probabilidade de observar a amostra obtida. Para uma Poisson, o estimador de máxima verossimilhança de λ também é a média amostral. A variância do estimador depende da informação de Fisher e do tamanho da amostra.

## Séries temporais e VAR

- Uma série é estacionária quando média e variância são constantes no tempo e não há tendência ou sazonalidade sistemática.
- Em um VAR de ordem p, cada variável é modelada como função linear das defasagens de todas as variáveis do sistema.
- Para previsões com VAR, a estacionariedade das séries é uma condição relevante; séries não estacionárias exigem tratamento adequado.

## Dados em painel

- **Efeitos fixos:** as características individuais não observáveis e constantes no tempo podem estar correlacionadas com as explicativas.
- **Efeitos aleatórios:** as diferenças individuais não observadas são tratadas como componentes aleatórios, tipicamente não correlacionadas com as explicativas.

## Processos estocásticos

Em uma cadeia de Markov, a probabilidade de transição para o próximo estado depende do estado atual, não de toda a sequência passada. Essa é a propriedade markoviana.

## Como a banca cobra

A questão costuma comparar métodos de estimação, afirmar que uma série não precisa ser estacionária ou trocar as hipóteses de efeitos fixos e aleatórios. Leia com atenção as palavras “necessário”, “suficiente” e “não correlacionado”.

## Checklist rápido

- Método dos momentos: iguale E[X] à média amostral.
- Poisson: E[X] = Var[X] = λ.
- VAR: defasagens de todas as variáveis.
- Painel: fixos versus aleatórios depende da correlação com as explicativas.
- Markov: o futuro depende do presente, não de todo o passado.
