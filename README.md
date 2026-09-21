# Análise de medições de sensor: monitoramento térmico de transformador

Programa que recebe uma sequência de medições (horário e valor) e informa:

- quantas medições são **válidas** e quantas são **inválidas**;
- **mínimo, máximo e média**, considerando apenas as válidas;
- as **mudanças bruscas** entre medições válidas consecutivas, isto é, quando `abs(atual - anterior) > limite`, com o limite informado pelo usuário.

Uma medição é inválida quando o valor é ausente, não numérico, `NaN` ou infinito. Medições inválidas são contadas, mas ficam fora das estatísticas e **não interrompem a comparação**: em `10.0 → (sem valor) → 20.0`, a comparação é entre 10.0 e 20.0.

O projeto faz parte do processo seletivo do LAIIC/UFJF e usa como cenário a temperatura de um transformador de distribuição (ver [Contexto](#contexto)). Os dados podem vir de um arquivo CSV ou de um simulador embutido.

## Como executar

Requer Python 3.10 ou superior. Execute os comandos **na raiz do repositório** (é dela que o Python encontra o pacote `sensor_monitor`), no PowerShell:

```powershell
py -m pip install -r requirements.txt        # só a interface gráfica precisa (matplotlib)
```

**Terminal.** Sem argumentos, usa o simulador e o limite padrão de 5.0; `--threshold` ajusta o limite e `--input` lê um CSV.

```powershell
py main.py                                               # pergunta a semente
py main.py --threshold 5 --input examples/exemplo_briefing.csv
py main.py --seed 17                                     # semente fixa, sem perguntar
Get-Content medicoes.csv | py main.py --input -          # entrada padrão
```

O simulador é aleatório: cada semente gera uma sequência diferente. Rodando `py main.py` num terminal, o programa pergunta qual semente usar:

```text
Semente do simulador (Enter para sortear):
```

Pressionar Enter sorteia uma. O cabeçalho da saída sempre informa a semente usada, então dá para repetir um caso interessante digitando o mesmo número na próxima execução, ou passando `--seed`. A opção `--seed` pula a pergunta, o que é o necessário em scripts. Quando a entrada padrão não é um terminal (execução automatizada, comando com `|`), a pergunta é omitida e a semente é sorteada.

Saída para o exemplo do briefing (`10:00→10.0; 10:05→11.5; 10:10→sem valor; 10:15→18.0; 10:20→17.5`):

```text
Análise das medições de examples/exemplo_briefing.csv
Medições válidas: 4
Medições inválidas: 1

Horário      Valor  Observação
-------  ---------  ------------------------
10:00     10.00 °C
10:05     11.50 °C
10:10    sem dados
10:15     18.00 °C  mudança brusca (6.50 °C)
10:20     17.50 °C

Valor mínimo: 10.00 °C
Valor máximo: 18.00 °C
Valor médio: 14.25 °C
Mudanças bruscas: 1
```

**Interface gráfica** (opcional): campo do limite, botões *Abrir CSV...* e *Usar simulação*, resumo (válidas, inválidas, mínimo, máximo, média, mudanças bruscas), série temporal, box plot e tabela das mudanças bruscas.

```powershell
py -m sensor_monitor.dashboard
py -m sensor_monitor.dashboard --input examples/exemplo_briefing.csv
```

**Formato do CSV.** Duas colunas, `horário,valor`. O cabeçalho é opcional, linhas em branco são ignoradas, e valor vazio, `NA` ou texto não numérico contam como inválidos. Uma linha sem horário ou com colunas a mais interrompe a leitura com uma mensagem de erro que indica o número da linha (código de saída 2).

```text
timestamp,value
10:00,10.0
10:10,
```

## Como a solução foi organizada

```text
sensor_monitor/
  models.py      Measurement (com a regra de validade), SuddenChange, AnalysisResult
  analyzer.py    regra do briefing: contagem, estatísticas e mudanças bruscas
  csv_input.py   leitura de CSV (arquivo ou entrada padrão)
  simulator.py   sequência térmica aleatória (20 leituras, com falhas e picos ocasionais)
  report.py      formatação dos números e do resumo
  plotting.py    série temporal e box plot (Matplotlib)
  cli.py         interface de terminal
  dashboard.py   interface gráfica (Tkinter + Matplotlib)
main.py          ponto de entrada (executa a interface de terminal)
examples/        exemplo_briefing.csv
cpp/             adaptador C++ opcional (ver abaixo)
```

A lógica de análise ([analyzer.py](sensor_monitor/analyzer.py)) não conhece a origem dos dados nem a apresentação. Simulador, CSV, terminal e interface gráfica dependem dela, e não o contrário. Assim, o simulador pode ser trocado por uma fonte real sem alterar a análise.

O limite é uma **diferença** entre leituras consecutivas, não uma temperatura máxima. Um limite negativo, `NaN` ou infinito é rejeitado. Uma mudança brusca indica um evento que merece investigação e não declara falha do equipamento.

## Testes realizados

A verificação foi **manual**, executando o programa no terminal. O projeto não tem suíte de testes automatizados. A tabela registra os casos executados e o que foi observado em cada um; todos são reproduzíveis, já que a semente fixa os dados do simulador.

| Caso | Comando | Resultado observado |
| --- | --- | --- |
| Exemplo do briefing | `py main.py --input examples/exemplo_briefing.csv` | 4 válidas, 1 inválida, mín 10,00 °C, máx 18,00 °C, média 14,25 °C, 1 mudança |
| Simulação típica | `py main.py --seed 17` | 19 válidas, 1 inválida, pico de 102,00 °C, 2 mudanças: a subida e o retorno |
| Mudança através de uma falha | `py main.py --seed 39` | 6 mudanças; a de 10:30→10:40 é detectada por cima do `sem dados` de 10:35 |
| Operação sem anomalia | `py main.py --seed 14` | 20 válidas, 0 inválidas, 0 mudanças; a coluna *Observação* não aparece |
| Várias falhas do sensor | `py main.py --seed 42` | 16 válidas, 4 inválidas, 0 mudanças; as falhas não interrompem a análise |
| Limite maior, mesmos dados | `py main.py --seed 39 --threshold 25` | as 6 mudanças caem para 2, e as temperaturas são as mesmas |
| Reprodutibilidade | `py main.py --seed 99`, duas vezes | saída idêntica |
| Aleatoriedade | `py main.py`, duas vezes | sequências diferentes |
| Pergunta da semente | `py main.py` num terminal | número digitado é usado; Enter sorteia; texto inválido avisa e pergunta de novo; Ctrl+C segue com semente sorteada |
| Execução sem terminal | `"" \| py main.py` | não pergunta e não trava: sorteia a semente |
| Cabeçalho, `NA` e campo vazio | `"horario,valor", "10:00,10.0", "10:05,NA", "10:10,", "10:15,20.0" \| py main.py --input -` | 2 válidas, 2 inválidas; a mudança de 10,00 °C é detectada através de **duas** falhas seguidas |
| Diferença igual ao limite | `"10:00,10.0", "10:05,15.0" \| py main.py --input -` | 0 mudanças — a comparação com o limite é `>` estrita |
| Diferença logo acima do limite | `"10:00,10.0", "10:05,15.01" \| py main.py --input -` | 1 mudança |
| Queda brusca | `"10:00,20.0", "10:05,10.0" \| py main.py --input -` | 1 mudança — vale o valor absoluto, não só a subida |
| Uma única medição válida | `"10:00,10.0" \| py main.py --input -` | 0 mudanças; mínimo, máximo e média iguais |
| Nenhuma medição válida | `"10:00,NA", "10:05,texto" \| py main.py --input -` | `sem dados` nas três estatísticas, sem erro |
| Limite negativo | `py main.py --threshold -1` | `Erro: O limite deve ser um número finito maior ou igual a zero.`, saída 2 |
| Arquivo inexistente | `py main.py --input nao_existe.csv` | `Erro: [Errno 2] No such file or directory: 'nao_existe.csv'`, saída 2 |
| Linha com colunas a mais | `"10:00,10.0", "10:05,11.5,extra" \| py main.py --input -` | `Erro: Linha 2: esperado 'horário,valor', recebido '10:05,11.5,extra'.`, saída 2 |

**Fora do alcance destes testes:** a interface gráfica foi verificada apenas quanto a iniciar sem erro — os gráficos (série temporal e box plot) não foram conferidos visualmente. O adaptador C++ tem verificação própria, descrita na seção seguinte.

## Adaptador C++ (opcional)

[cpp/src/edge_adapter.cpp](cpp/src/edge_adapter.cpp) representa a fronteira entre um equipamento e o analisador. Lê `horário,valor` pela entrada padrão e escreve CSV normalizado: valores vazios, não numéricos ou infinitos viram `NA`, e linhas sem horário são ignoradas com um aviso no `stderr`. A saída é lida diretamente pela CLI:

```powershell
cmake -S cpp -B build
cmake --build build
Get-Content medicoes.csv | .\build\edge_adapter.exe | py main.py --threshold 5 --input -
```

Com MinGW o executável fica em `build\edge_adapter.exe`. Com Visual Studio, em `build\Debug\edge_adapter.exe`. Sem CMake, `g++ -std=c++17 cpp/src/edge_adapter.cpp -o edge_adapter.exe` produz o mesmo resultado. O adaptador não é necessário para a análise em Python. Não há teste automatizado para o C++, e a verificação foi manual.

## Contexto

O projeto se insere em pesquisa aplicada em IA, sistemas embarcados e energia (computação de borda para monitoramento e manutenção preditiva). O simulador substitui, nesta etapa, um sensor térmico real.

Minhas idéias de expansão (possíveis de explorar na IC): histórico persistente das leituras, modelos leves de detecção de anomalias, comunicação MQTT/industrial e execução em dispositivo de borda. A solução é um protótipo e não substitui um sistema de proteção industrial certificado.
