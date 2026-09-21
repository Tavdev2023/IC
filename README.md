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
py -m pip install -r requirements.txt        # matplotlib, usado pelos gráficos
```

A instalação é necessária para a interface gráfica. A análise pelo terminal não usa o Matplotlib e roda sem ela.

**Interface gráfica.** `py main.py` abre a janela do monitor:

```powershell
py main.py
py main.py --seed 17                                     # já inicia com essa semente
py main.py --input examples/exemplo_briefing.csv         # já abre esse CSV
```

A janela traz o campo do limite, o campo da semente, os botões *Usar simulação* e *Abrir CSV...*, o resumo (válidas, inválidas, mínimo, máximo, média, mudanças bruscas), a série temporal, o box plot e a tabela com todas as medições, onde as mudanças bruscas aparecem marcadas na coluna *Observação*. Deixar a semente em branco sorteia uma e escreve no campo qual foi usada, então dá para repetir um caso interessante.

**Terminal.** A mesma análise sem interface, útil para scripts e para redirecionar a saída:

```powershell
py -m sensor_monitor.cli                                 # pergunta a semente
py -m sensor_monitor.cli --threshold 5 --input examples/exemplo_briefing.csv
py -m sensor_monitor.cli --seed 17                       # semente fixa, sem perguntar
Get-Content medicoes.csv | py -m sensor_monitor.cli --input -    # entrada padrão
```

Sem argumentos, o terminal usa o simulador e o limite padrão de 5.0. O simulador é aleatório: cada semente gera uma sequência diferente. Num terminal, o programa pergunta qual semente usar:

```text
Semente do simulador (Enter para sortear):
```

Pressionar Enter sorteia uma. O cabeçalho da saída sempre informa a semente usada, então dá para repetir um caso interessante passando `--seed`. Essa opção também pula a pergunta, o que é o necessário em scripts. Quando a entrada padrão não é um terminal (execução automatizada, comando com `|`), a pergunta é omitida e a semente é sorteada.

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
main.py          ponto de entrada (abre a interface gráfica)
examples/        exemplo_briefing.csv
cpp/             adaptador C++ opcional (ver abaixo)
```

A lógica de análise ([analyzer.py](sensor_monitor/analyzer.py)) não conhece a origem dos dados nem a apresentação. Simulador, CSV, terminal e interface gráfica dependem dela, e não o contrário. Assim, o simulador pode ser trocado por uma fonte real sem alterar a análise.

O limite é uma **diferença** entre leituras consecutivas, não uma temperatura máxima. Um limite negativo, `NaN` ou infinito é rejeitado. Uma mudança brusca indica um evento que merece investigação e não declara falha do equipamento.

## Testes realizados

A verificação foi **manual**. O projeto não tem suíte de testes automatizados. As tabelas registram os casos executados e o que foi observado em cada um; todos são reproduzíveis, já que a semente fixa os dados do simulador.

### Análise (terminal)

| Caso | Comando | Resultado observado |
| --- | --- | --- |
| Exemplo do briefing | `py -m sensor_monitor.cli --input examples/exemplo_briefing.csv` | 4 válidas, 1 inválida, mín 10,00 °C, máx 18,00 °C, média 14,25 °C, 1 mudança |
| Simulação típica | `py -m sensor_monitor.cli --seed 17` | 19 válidas, 1 inválida, pico de 102,00 °C, 2 mudanças: a subida e o retorno |
| Mudança através de uma falha | `py -m sensor_monitor.cli --seed 39` | 6 mudanças; a de 10:30→10:40 é detectada por cima do `sem dados` de 10:35 |
| Operação sem anomalia | `py -m sensor_monitor.cli --seed 14` | 20 válidas, 0 inválidas, 0 mudanças; a coluna *Observação* não aparece |
| Várias falhas do sensor | `py -m sensor_monitor.cli --seed 42` | 16 válidas, 4 inválidas, 0 mudanças; as falhas não interrompem a análise |
| Limite maior, mesmos dados | `py -m sensor_monitor.cli --seed 39 --threshold 25` | as 6 mudanças caem para 2, e as temperaturas são as mesmas |
| Reprodutibilidade | `py -m sensor_monitor.cli --seed 99`, duas vezes | saída idêntica |
| Aleatoriedade | `py -m sensor_monitor.cli`, duas vezes | sequências diferentes |
| Pergunta da semente | `py -m sensor_monitor.cli` num terminal | número digitado é usado; Enter sorteia; texto inválido avisa e pergunta de novo; Ctrl+C segue com semente sorteada |
| Execução sem terminal | `"" \| py -m sensor_monitor.cli` | não pergunta e não trava: sorteia a semente |
| Cabeçalho, `NA` e campo vazio | `"horario,valor", "10:00,10.0", "10:05,NA", "10:10,", "10:15,20.0" \| py -m sensor_monitor.cli --input -` | 2 válidas, 2 inválidas; a mudança de 10,00 °C é detectada através de **duas** falhas seguidas |
| Diferença igual ao limite | `"10:00,10.0", "10:05,15.0" \| py -m sensor_monitor.cli --input -` | 0 mudanças — a comparação com o limite é `>` estrita |
| Diferença logo acima do limite | `"10:00,10.0", "10:05,15.01" \| py -m sensor_monitor.cli --input -` | 1 mudança |
| Queda brusca | `"10:00,20.0", "10:05,10.0" \| py -m sensor_monitor.cli --input -` | 1 mudança — vale o valor absoluto, não só a subida |
| Uma única medição válida | `"10:00,10.0" \| py -m sensor_monitor.cli --input -` | 0 mudanças; mínimo, máximo e média iguais |
| Nenhuma medição válida | `"10:00,NA", "10:05,texto" \| py -m sensor_monitor.cli --input -` | `sem dados` nas três estatísticas, sem erro |
| Limite negativo | `py -m sensor_monitor.cli --threshold -1` | `Erro: O limite deve ser um número finito maior ou igual a zero.`, saída 2 |
| Arquivo inexistente | `py -m sensor_monitor.cli --input nao_existe.csv` | `Erro: [Errno 2] No such file or directory: 'nao_existe.csv'`, saída 2 |
| Linha com colunas a mais | `"10:00,10.0", "10:05,11.5,extra" \| py -m sensor_monitor.cli --input -` | `Erro: Linha 2: esperado 'horário,valor', recebido '10:05,11.5,extra'.`, saída 2 |

### Interface gráfica

Verificada construindo a janela sem exibi-la e inspecionando os widgets, e depois abrindo a janela de verdade.

| Caso | Como | Resultado observado |
| --- | --- | --- |
| Abre sem erro | `py main.py --seed 17` | janela permanece aberta, sem exceção |
| Tabela completa | inspeção dos widgets | 20 linhas, 1 marcada `sem dados`, 2 marcadas como mudança brusca |
| Mesmos números do terminal | comparação com `py -m sensor_monitor.cli --seed 17` | linha a linha idêntica, inclusive `10:25 102,00 °C` e as duas mudanças |
| Limite aplicado na janela | limite alterado para 50 | as marcações de mudança brusca somem |
| Semente reproduz | semente 17 carregada duas vezes | mesmos valores nas 20 linhas |
| Semente em branco | botão *Usar simulação* | sorteia e escreve a semente usada no campo |

**Fora do alcance destes testes:** a aparência dos gráficos (série temporal e box plot) não foi conferida visualmente — os testes confirmam que são desenhados sem erro, não que estejam legíveis ou bem dimensionados. Os botões *Abrir CSV...* e as caixas de erro também não foram exercitados por clique. O adaptador C++ tem verificação própria, descrita na seção seguinte.

## Adaptador C++ (opcional)

[cpp/src/edge_adapter.cpp](cpp/src/edge_adapter.cpp) representa a fronteira entre um equipamento e o analisador. Lê `horário,valor` pela entrada padrão e escreve CSV normalizado: valores vazios, não numéricos ou infinitos viram `NA`, e linhas sem horário são ignoradas com um aviso no `stderr`. A saída é lida diretamente pela CLI:

```powershell
cmake -S cpp -B build
cmake --build build
Get-Content medicoes.csv | .\build\edge_adapter.exe | py -m sensor_monitor.cli --threshold 5 --input -
```

Com MinGW o executável fica em `build\edge_adapter.exe`. Com Visual Studio, em `build\Debug\edge_adapter.exe`. Sem CMake, `g++ -std=c++17 cpp/src/edge_adapter.cpp -o edge_adapter.exe` produz o mesmo resultado. O adaptador não é necessário para a análise em Python. Não há teste automatizado para o C++, e a verificação foi manual.

## Contexto

O projeto se insere em pesquisa aplicada em IA, sistemas embarcados e energia (computação de borda para monitoramento e manutenção preditiva). O simulador: **simulator.py** substitui, nesta etapa, um sensor térmico real.

Minhas idéias de expansão (possíveis de explorar na IC): histórico persistente das leituras, modelos leves de detecção de anomalias, comunicação industrial e execução em dispositivo de borda. 

Considerações: A solução atual é um protótipo desenvolvido em conjunto com Claude Code e não substitui um sistema de proteção industrial certificado.
