---
title: "Redes, cloud, virtualização e sistemas operacionais"
slug: ti-redes-cloud-so
summary: "HTTP, LDAP, LAN/WAN, SDN, IaaS, live migration e SO."
topics:
  - infraestrutura-ti
  - protocolos-redes
  - cloud-virtualizacao-so
tags:
  - infra-protocolos-redes
  - infra-cloud-so
source: "Resumo gerado para o Study App"
source_kind: generated
review_status: approved
---

## Protocolos

- **HTTP:** camada de aplicação, usado para web; e-mail usa SMTP, IMAP e POP.
- **LDAP:** serviço de diretório, comum no Active Directory, usado para autenticação.
- **LAN:** mesma localidade física.
- **WAN:** interliga LANs geograficamente distribuídas.
- **SDN:** separa plano de controle e plano de dados; tende a trazer flexibilidade, escalabilidade e gestão centralizada, não o contrário.

## Cloud e virtualização

- **IaaS:** infraestrutura (VMs, redes, armazenamento). Plataforma, middleware e banco gerenciado são típicos de PaaS.
- **Live migration:** move uma VM em execução, com pré-cópia de memória.
- **Alta disponibilidade:** pouco downtime e recuperação rápida.
- **Failover:** assume o recurso redundante após falha. **Failback:** retorna ao recurso original.

## Windows e Linux

- Windows Admin Center é interface web de administração, inclusive de clusters hiperconvergentes.
- `dpkg` instala pacotes, mas não resolve todas as dependências automaticamente como o `apt`.

## Como a banca cobra

Troca IaaS por PaaS, failover por failback, lista vantagens de SDN como desvantagens e atribui ao `dpkg` resolução automática de dependências.

## Checklist rápido

- HTTP não é protocolo de e-mail.
- LAN local; WAN interliga LANs.
- IaaS = infraestrutura.
- Failover assume; failback retorna.
