---
title: "Kubernetes, contêineres e serverless"
slug: ti-kubernetes-serverless
summary: "Pods, kube-scheduler, FaaS, BaaS e modelos gerenciados."
topics:
  - engenharia-de-software
  - microsservicos-serverless
  - infraestrutura-ti
  - kubernetes-containers
tags:
  - es-serverless
  - infra-kubernetes
source: "Resumo gerado para o Study App"
source_kind: generated
review_status: approved
---

## Kubernetes

- Um **pod** é a menor unidade executável e sempre é agendado em um nó.
- O **kube-scheduler** escolhe o nó para o pod; o escalonamento automático de réplicas é papel do HPA e de outros controladores.
- O Kubernetes pode usar diferentes runtimes compatíveis com CRI, como Containerd e CRI-O; Docker não é obrigatório.
- Em Kubernetes serverless, o provedor gerencia nós, kubelets e infraestrutura; a equipe não administra pods como se fossem servidores.

## Serverless

- **FaaS:** funções orientadas a eventos, executadas em contêineres stateless gerenciados.
- **BaaS:** serviços de terceiros consumidos por API, como autenticação, banco e criptografia.
- O provedor gerencia infraestrutura e escala; o foco da equipe é o código.

## YAML

Um manifesto com `kind: Service` cria um serviço, não um deployment. Para deployment, o `kind` precisa ser `Deployment`.

## Como a banca cobra

Confunde Service com Deployment, atribui ao kube-scheduler o papel de HPA e afirma que o cliente precisa gerenciar servidores no serverless.

## Checklist rápido

- Pod sempre roda em nó.
- kube-scheduler agenda; HPA escala.
- FaaS: evento + stateless.
- BaaS: serviços via API.
- `kind: Service` ≠ Deployment.
