# Jarvis v3

Assistente de voz local para macOS com Apple Silicon. Fale assim que
aparecer `[LISTENING]`. O Silero VAD detecta a fala e espera uma pausa
antes de passar o segmento ao Whisper Small. O Ollama responde com
Qwen3 8B, e o Piper lê a resposta com a voz brasileira Faber. O histórico bruto
e as memórias explícitas ficam em `data/jarvis.sqlite3`. Para sair, pressione
Ctrl+C ou diga “sair” ou “encerrar”.

## Preparação

Use Python 3.13 no venv do projeto. O Python 3.15 do antigo
`jarvis_env` não encontrou uma distribuição compatível do ONNX Runtime
para o Piper.

Para recriar o ambiente com o `uv` disponível:

```sh
UV_PYTHON_INSTALL_DIR="$PWD/.jarvis-python" uv venv --python 3.13 --seed .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

O `requirements.txt` fixa as versões de MLX e ONNX Runtime usadas no
macOS 26, além do par `huggingface-hub` e `click` validado no venv.

Baixe os pesos uma vez, a partir da raiz do projeto:

```sh
mkdir -p voices
python -m piper.download_voices --download-dir voices pt_BR-faber-medium
python -c 'from huggingface_hub import snapshot_download; snapshot_download("mlx-community/whisper-small-mlx", local_dir="models/whisper-small", allow_patterns=["config.json", "weights.safetensors", "weights.npz"])'
mkdir -p models/silero
curl -fLsS -o models/silero/silero_vad.onnx https://raw.githubusercontent.com/snakers4/silero-vad/v6.2/src/silero_vad/data/silero_vad.onnx
```

Com o Ollama em execução, verifique o modelo com `ollama list`. Caso ele
ainda não esteja instalado, execute `ollama pull qwen3:8b`. Os downloads
exigem internet. Em execução, o Jarvis lê os pesos locais e consulta apenas
o Ollama em `127.0.0.1:11434`.

## Execução

```sh
source .venv/bin/activate
python main.py --check
python main.py
```

## Interface

Em outro terminal, inicie o frontend:

```sh
cd frontend
npm install
npm run dev
```

O frontend conecta automaticamente ao backend WebSocket local (`127.0.0.1:8765`),
iniciado junto com `main.py`. Use o botão de modo no topo para alternar para a
demonstração; `?demo=true` também abre diretamente nesse modo.
Durante a fala, o botão de microfone interrompe a reprodução e volta à escuta;
toque nele antes de falar uma correção. O terminal registra tempos por etapa
com o prefixo `[TEMPO]` para ajudar a localizar atrasos.
O botão de microfone controla a escuta; a captura continua no backend Python.

## Abrir pelo Dock

Depois de preparar o projeto, abra `Jarvis.app` na pasta do projeto. O app inicia
Ollama se necessário, sobe o backend e o frontend e abre a interface no navegador
padrão. Para fixá-lo no Dock, arraste `Jarvis.app` do Finder para o Dock.
Os registros de inicialização ficam em `data/logs/`; o log do backend guarda
erros, sem salvar as falas da conversa.

O Jarvis também pode fazer uma busca web quando você pedir explicitamente uma
pesquisa ou informação atual. A busca usa os resultados HTML do DuckDuckGo, sem
chave de API; o texto da consulta é enviado ao DuckDuckGo e os resultados são
tratados como conteúdo externo não confiável.

O modo `--check` carrega Whisper, Piper e Silero e verifica um bloco de
silêncio, sem abrir o microfone ou enviar mensagens ao Ollama.
O modo normal usa a entrada e a saída de áudio padrão do macOS.
Se solicitado pelo macOS, permita acesso ao microfone no aplicativo que
executa o Jarvis.

- `--silence-ms 700` define a pausa que encerra a fala, de 200 a 5.000 ms.
- `--vad-threshold 0.5` ajusta a sensibilidade. Aumente o valor se ruídos
  estiverem abrindo turnos.
- A captura usa blocos mono de 32 ms e limita segmentos a cerca de 25 s.
  O microfone fecha em `PROCESSING` e `SPEAKING`, e reabre em
  `LISTENING` após a reprodução. Fale novamente quando voltar à escuta.

- `mlx-whisper` executa o Whisper Small em MLX.
- `piper-tts` executa a voz Faber com ONNX Runtime.
- O Silero VAD v6.2 reutiliza o ONNX Runtime para detectar voz na CPU.
- `sounddevice` e `numpy` capturam e reproduzem PCM.
- `requests` envia o histórico à API de chat do Ollama.
