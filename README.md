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

**Terminal.** O limite é obrigatório (`--threshold`). Sem `--input`, usa-se o simulador.

```powershell
py -m sensor_monitor.cli --threshold 5 --input examples/exemplo_briefing.csv
py -m sensor_monitor.cli --threshold 10                  # dados simulados
Get-Content medicoes.csv | py -m sensor_monitor.cli --threshold 5 --input -   # entrada padrão
```

Saída para o exemplo do briefing (`10:00→10.0; 10:05→11.5; 10:10→sem valor; 10:15→18.0; 10:20→17.5`):

```text
Análise das medições de examples/exemplo_briefing.csv
Medições válidas: 4
Medições inválidas: 1
Valor mínimo: 10.00
Valor máximo: 18.00
Valor médio: 14.25
Mudanças bruscas: 1
- 10:05 -> 10:15: diferença absoluta 6.50
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

**Testes** (qualquer um dos comandos abaixo, a partir da raiz):

```powershell
py -m unittest -v
py -m unittest discover -s tests -v
```

## Como a solução foi organizada

```text
sensor_monitor/
  models.py      Measurement (com a regra de validade), SuddenChange, AnalysisResult
  analyzer.py    regra do briefing: contagem, estatísticas e mudanças bruscas
  csv_input.py   leitura de CSV (arquivo ou entrada padrão)
  simulator.py   sequência térmica determinística (20 leituras, 1 ausente, 1 pico de 101.5 °C)
  report.py      formatação dos números e do resumo
  plotting.py    série temporal e box plot (Matplotlib)
  cli.py         interface de terminal
  dashboard.py   interface gráfica (Tkinter + Matplotlib)
tests/           testes automatizados (unittest)
examples/        exemplo_briefing.csv
cpp/             adaptador C++ opcional (ver abaixo)
```

A lógica de análise ([analyzer.py](sensor_monitor/analyzer.py)) não conhece a origem dos dados nem a apresentação. Simulador, CSV, terminal e interface gráfica dependem dela, e não o contrário. Assim, o simulador pode ser trocado por uma fonte real sem alterar a análise.

O limite é uma **diferença** entre leituras consecutivas, não uma temperatura máxima. Um limite negativo, `NaN` ou infinito é rejeitado. Uma mudança brusca indica um evento que merece investigação e não declara falha do equipamento.

## Casos usados para verificar o funcionamento

Os 28 testes automatizados cobrem:

| Caso | Onde |
| --- | --- |
| Exemplo do briefing (4 válidas, 1 inválida, mín 10, máx 18, média 14,25, 1 mudança brusca) | `test_csv_input`, `test_cli` |
| Simulador com limite 10: 19 válidas, 1 inválida, pico de 101,5 °C e retorno detectados (10:50→10:55 e 10:55→11:00) | `test_analyzer`, `test_cli` |
| Valor ausente entre duas válidas não interrompe a comparação, e a mudança através dele é detectada | `test_analyzer` |
| Diferença **igual** ao limite não é mudança brusca (`>` estrito); queda também conta (valor absoluto) | `test_analyzer` |
| `NaN`, infinito, texto e `bool` como valor são inválidos, sem erro | `test_analyzer` |
| Sem medições válidas: sem estatísticas ("sem dados"); com uma só válida: sem mudanças | `test_analyzer`, `test_cli` |
| Limite negativo, `NaN` ou infinito rejeitado (CLI retorna erro) | `test_analyzer`, `test_cli` |
| CSV: cabeçalho opcional, valores vazios/`NA`, CRLF, BOM, linha malformada com número da linha, arquivo inexistente, entrada padrão | `test_csv_input`, `test_cli` |
| Gráficos gerados a partir das válidas, com destaque correto mesmo com horários repetidos, e resumo com mínimo e máximo | `test_plotting` |

## Adaptador C++ (opcional)

[cpp/src/edge_adapter.cpp](cpp/src/edge_adapter.cpp) representa a fronteira entre um equipamento e o analisador. Lê `horário,valor` pela entrada padrão e escreve CSV normalizado: valores vazios, não numéricos ou infinitos viram `NA`, e linhas sem horário são ignoradas com um aviso no `stderr`. A saída é lida diretamente pela CLI:

```powershell
cmake -S cpp -B build
cmake --build build
Get-Content medicoes.csv | .\build\edge_adapter.exe | py -m sensor_monitor.cli --threshold 5 --input -
```

Com MinGW o executável fica em `build\edge_adapter.exe`. Com Visual Studio, em `build\Debug\edge_adapter.exe`. Sem CMake, `g++ -std=c++17 cpp/src/edge_adapter.cpp -o edge_adapter.exe` produz o mesmo resultado. O adaptador não é necessário para a análise em Python. Não há teste automatizado para o C++, e a verificação foi manual.

## Contexto

O projeto se insere em pesquisa aplicada em IA, sistemas embarcados e energia (computação de borda para monitoramento e manutenção preditiva). O simulador substitui, nesta etapa, um sensor térmico real.

Próximas etapas possíveis: histórico persistente das leituras, modelos leves de detecção de anomalias, comunicação MQTT/industrial e execução em dispositivo de borda. A solução é um protótipo e não substitui um sistema de proteção industrial certificado.
