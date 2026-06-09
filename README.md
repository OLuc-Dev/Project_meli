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

A interface agora é um protótipo navegável mais completo: permite upload de CSV, colar exemplos, escolher cenários prontos, ver gráfico reconstruído, KPIs, alertas, recomendações e prévia de imagem do gráfico. Ela é estática e não exige backend. Basta abrir o arquivo:

```bash
python -m http.server 8000 --directory web
```

Depois acesse `http://localhost:8000`. A tela já abre com um exemplo crítico carregado, mas você também pode clicar nos cenários prontos, enviar CSV ou colar seus próprios exemplos.

## Como validar seus exemplos

1. Abra a interface web.
2. Cole um CSV real ou simplificado no campo **Ou cole aqui o seu exemplo**.
3. Clique em **Analisar dados colados**.
4. Use a área de perguntas para testar frases como “tem risco de capacidade?”, “as pessoas acompanham?” ou “a produtividade caiu?”.
5. Se quiser mostrar um print do dashboard, use o upload de imagem para prévia visual; a análise exata continua vindo do CSV.

## Validação contra conflitos de código

O projeto tem um teste de integridade para evitar que marcadores de conflito de merge, como `<<<<<<<`, `=======` e `>>>>>>>`, fiquem dentro dos arquivos versionados. Também há uma validação de sintaxe do JavaScript embutido na página web quando Node.js está disponível.

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

## Como publicar no GitHub Pages

A página está pronta para ser publicada pelo GitHub Pages usando GitHub Actions. O workflow em `.github/workflows/deploy-pages.yml` publica automaticamente a pasta `web/`, que contém o protótipo estático.

Para ver online:

1. Suba esta branch para o GitHub.
2. No repositório, abra **Settings > Pages**.
3. Em **Build and deployment**, selecione **GitHub Actions** como fonte.
4. Rode o workflow **Deploy Capacity Vision web** pela aba **Actions** ou faça push em `main`, `master` ou `work`.
5. Quando o deploy terminar, a URL pública aparecerá no resumo do workflow.

Também adicionei `web/.nojekyll` para garantir que o GitHub Pages sirva todos os arquivos estáticos sem processamento do Jekyll.
