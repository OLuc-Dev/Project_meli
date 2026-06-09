# Capacity Vision ML

MVP para a área de Planejamento/Capacidades do Mercado Livre analisar **pacotes, pessoas, forecast e capacidade** usando dados estruturados. A versão prioriza qualidade: primeiro calcula em cima de CSVs confiáveis, depois gera uma leitura executiva em linguagem natural.

## Por que esta versão é a melhor para qualidade?

A análise por foto ou print de gráfico é útil para demonstração, mas pode errar valores quando a imagem está borrada, sem escala clara ou com muitas séries. Este MVP usa dados estruturados para calcular percentuais, gaps e alertas com mais precisão. A camada de linguagem natural entra depois, para explicar os resultados de forma simples.

## Funcionalidades

- Leitura de CSV com cabeçalhos em português ou inglês.
- Cálculo de variação de pacotes, pessoas e produtividade.
- Detecção de tendência de alta, queda ou estabilidade.
- Alertas para gap entre volume e headcount.
- Alertas de capacidade próxima do limite ou excedida.
- Diagnóstico por semáforo: Verde, Amarelo ou Vermelho.
- Perguntas simples em linguagem natural pelo CLI ou pela interface web.

## Colunas aceitas no CSV

Obrigatórias:

- `periodo`, `data`, `mes`, `date` ou `period`.
- `pacotes`, `volume`, `packages` ou `shipments`.
- `pessoas`, `headcount`, `hc`, `fte` ou `people`.

Opcionais:

- `forecast`, `previsto`, `previsao` ou `planejado`.
- `capacidade`, `capacity` ou `capacidade_planejada`.

Exemplo disponível em [`sample_data/capacity_sample.csv`](sample_data/capacity_sample.csv).

## Como rodar a análise pelo terminal

```bash
python -m capacity_vision.cli sample_data/capacity_sample.csv
```

Com pergunta em linguagem natural:

```bash
python -m capacity_vision.cli sample_data/capacity_sample.csv --question "O volume está subindo ou caindo?"
```

## Como abrir a interface web

A interface é estática e não exige backend. Basta abrir o arquivo:

```bash
python -m http.server 8000 --directory web
```

Depois acesse `http://localhost:8000` e clique em **Usar exemplo** ou envie um CSV.

## Estrutura do projeto

```text
src/capacity_vision/analyzer.py  # motor analítico
src/capacity_vision/cli.py       # entrada por linha de comando
web/index.html                   # interface web estática
tests/test_analyzer.py           # testes automatizados
sample_data/capacity_sample.csv  # base de exemplo
```

## Próximos passos recomendados

1. Conectar o motor a uma base interna ou dashboard aprovado.
2. Adicionar ingestão de Excel além de CSV.
3. Integrar um modelo multimodal para interpretar prints de gráficos como apoio visual.
4. Usar um modelo de linguagem para gerar relatórios executivos semanais.
5. Criar simulações: “se o volume subir 20%, quantas pessoas preciso?”.
