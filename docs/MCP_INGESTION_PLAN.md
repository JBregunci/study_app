# Plano de ingestão com o MCP do PCI Concursos

Status: planejado; não implementado.

## Servidor

- URL: `https://mcp.pciconcursos.com.br/mcp`
- Tipo: remoto, público, somente consulta, sem login.
- Ferramentas disponíveis:
  - `buscar_por_cargo`
  - `buscar_por_cidade`
  - `listar_concursos`
  - `pesquisar_concursos`
  - `pesquisar_provas`

O MCP retorna informações públicas e **links de páginas** de provas; ele não entrega diretamente os PDFs. As páginas de download do PCI podem exigir captcha/JavaScript.

## Configuração futura

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "pci-concursos": {
      "type": "remote",
      "url": "https://mcp.pciconcursos.com.br/mcp",
      "enabled": true
    }
  }
}
```

Depois de alterar o `opencode.json`, reinicie o opencode.

## Objetivo

Usar o MCP para descobrir provas anteriores e alimentar o banco local com questões, gabaritos, classificação e materiais, reduzindo trabalho manual e evitando duplicidade.

## Fluxo proposto

1. **Descoberta**
   - Agente consulta `pesquisar_provas` por órgão, cargo, banca e ano.
   - Também pode usar as ferramentas de concursos para descobrir editais recentes.
   - Cada resultado gera um candidato com página de origem, órgão, banca, ano e cargo.

2. **Catálogo**
   - Candidato entra em uma fila de exames planejados.
   - Normalizar órgão, banca, edição e cargo.
   - Deduplicar contra `data/catalog/exams.json`.
   - Não criar exame até a prova ser realmente importada.

3. **Aquisição**
   - Preferir o CDN/site oficial da banca para obter prova e gabarito.
   - Usar o PCI como fallback ou como fonte de descoberta.
   - Se houver captcha, marcar como “download manual necessário” e não bloquear os demais.
   - Guardar PDFs em `data/sources/` (fora do git).

4. **Extração**
   - Usar pypdf/PyMuPDF para texto e imagens.
   - Separar itens, contextos, tabelas, código e figuras.
   - Extrair gabarito definitivo e anuladas.
   - Gerar um relatório de conferência por prova.

5. **Deduplicação**
   - Exame: chave normalizada de órgão + banca + ano + cargo + edital.
   - Questão: `external_id` e hash exato.
   - Duplicata exata: reutilizar questão e vincular ao novo exame.
   - Quase duplicata: sinalizar para revisão.
   - Rodar `make audit` antes de qualquer aprovação.

6. **Classificação**
   - Reutilizar temas/assuntos existentes.
   - Agente deve consultar o catálogo antes de propor tag nova.
   - Manter uma área e um assunto principal por questão.
   - Sugerir no máximo uma tag nova por lote e marcá-la para revisão.

7. **Explicações**
   - Gerar justificativas alinhadas ao gabarito oficial.
   - Marcar `explanation_source: generated`.
   - Importar como `draft`.
   - Amostragem humana antes de aprovar.

8. **Revisão e aprovação**
   - Fila mostrando conflitos, anuladas, baixa confiança e duplicatas.
   - Aprovar em lote ou individualmente.
   - Materiais só são publicados após revisão.

9. **Pós-importação**
   - Verificar cobertura de materiais.
   - Rodar testes, auditoria e smoke.
   - Atualizar estado e relatório da prova.

## Agentes e responsabilidades

- **Discovery agent:** consulta MCP, registra candidatos e fontes.
- **Extraction agent:** baixa/extrai texto, imagens e gabarito.
- **Curation agent:** classifica, deduplica e propõe materiais.
- **Explanation agent:** gera justificativas e marca proveniência.
- **Review agent/humano:** aprova, corrige e publica.
- **Checkpoint agent:** `make test`, `make audit`, docs, commit e push.

## Limites e cuidados

- MCP é beta e pode mudar.
- Consultas são somente leitura e não substituem o gabarito oficial.
- Respeitar termos de uso, limites de requisição e direitos sobre as provas.
- Não copiar comentários de terceiros; justificativas são geradas.
- Manter provenance: fonte, URL, número do item e status.
- Nunca aprovar automaticamente explicações geradas.
- Nunca apagar histórico ou questões sem autorização explícita.

## Métricas

- Provas descobertas, importadas e pendentes.
- Questões únicas, reutilizadas e duplicatas detectadas.
- Anuladas por prova.
- Cobertura de materiais.
- Taxa de questões com explicação gerada/revisada.

## Fases futuras

1. Configurar o MCP e testar as cinco ferramentas.
2. Criar catálogo de exames planejados.
3. Adaptar o extrator para múltiplos formatos de banca.
4. Implementar fila de revisão no app.
5. Processar um lote piloto de 2–3 provas.
6. Expandir com métricas e automação de checkpoint.

Até a configuração, o fluxo manual atual continua sendo a fonte de verdade.
