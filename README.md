# Projeto 6 - DTMF

O projeto contém duas aplicações independentes:

- `emissor.py`: solicita um número de 0 a 9, gera as duas frequências DTMF,
  reproduz o áudio e plota o sinal no tempo e na frequência.
- `receptor.py`: grava o áudio pelo microfone, calcula a FFT, encontra pelo
  menos cinco picos, identifica as duas frequências DTMF e informa o número.
- `projeto.py`: oferece um menu para abrir qualquer um dos lados.

## Instalação

O ambiente isolado deste projeto se chama `venv`. Para instalar em outro
computador com Python 3.10 ou superior, execute na pasta do projeto:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Execução em dois computadores

No computador que produzirá o áudio:

```powershell
.\venv\Scripts\python.exe emissor.py
```

No computador que captará o áudio:

```powershell
.\venv\Scripts\python.exe receptor.py
```

Primeiro inicie o receptor. Quando ele solicitar, faça o emissor começar a
tocar. Só então pressione ENTER no receptor, para não gravar silêncio.
O emissor toca por cinco segundos e o receptor grava por dois segundos.
Feche a janela dos gráficos para retornar ao menu.

Também é possível executar `.\venv\Scripts\python.exe projeto.py` e escolher
a função no menu.

## VS Code

Abra esta pasta no VS Code. As configurações em `.vscode` apontam para o
Python de `venv`, sem exigir instalação global das bibliotecas ou ativação
manual do ambiente. As extensões Python, Pylance e Python Debugger são
recomendadas em `.vscode/extensions.json`.

Pressione **F5** e selecione **DTMF: menu principal**, **DTMF: emissor** ou
**DTMF: receptor**. As perguntas aparecem no terminal integrado.
Se houver um terminal antigo aberto, abra um novo para receber o ambiente
configurado. Se o VS Code tiver outro interpretador selecionado anteriormente,
use **Python: Select Interpreter** e escolha `venv\Scripts\python.exe`.
As configurações de F5 já usam esse caminho explicitamente.

Em **Terminal > Executar Tarefa**, há opções para instalar as dependências e
testar o reconhecimento. Os testes também aparecem na aba de testes do VS Code.

## Microfone e saída de som

O programa usa os dispositivos padrão do Windows. A opção **3** do menu
lista os dispositivos e permite escolher o microfone e a saída por seus índices.
A escolha vale até fechar o programa; para usar os arquivos separadamente,
configure os dispositivos padrão no Windows. A taxa preferida é 44100 Hz;
se a placa não aceitar essa taxa, o programa tenta sua taxa padrão.

Se o microfone falhar, confira **Configurações > Privacidade e segurança >
Microfone** e a permissão para aplicativos da área de trabalho. Selecione o
microfone correto, retire o mudo e evite saturação de volume. Para transmitir
entre computadores, use os alto-falantes do emissor perto do microfone do receptor.

## Verificação sem equipamento de áudio

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes verificam os dez dígitos, sinais com ruído e silêncio nas taxas de
8000, 44100 e 48000 Hz, quantidade de picos, rejeição de sinais inválidos e
tratamento de erro na saída de som. A transmissão acústica entre dois aparelhos
precisa ser conferida com os equipamentos reais.

## Observação sobre as frequências

O código usa a grade DTMF padrão: 697, 770, 852 e 941 Hz nas linhas; 1209,
1336, 1477 e 1633 Hz nas colunas. Para o trabalho numérico são usadas somente
as colunas de 1209, 1336 e 1477 Hz.
