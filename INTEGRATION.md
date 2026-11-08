# Contratos de integração do Jarvis

## Plano

1. Implementar os módulos isolados em `frontend/` e `memory.py`/`tests/`.
2. Integrar memória e eventos no ciclo atual sem trocar STT, TTS, captura ou modelo Ollama.
3. Validar os testes de memória e o build/demo do frontend, então revisar fluxo, falhas e instruções locais.

## Limites de propriedade

- `frontend/`: interface React/Vite/Three.js, incluindo demonstração; sem alterações no backend.
- `memory.py` e `tests/`: armazenamento e testes de memória; sem alterações em `main.py`, `audio.py` ou nos modelos.
- `main.py`, `audio.py`, `requirements.txt`, `README.md` e este documento: integração pelo orquestrador.

## Memória Python

O módulo `memory.py` expõe `MemoryStore(db_path)` como context manager e métodos síncronos:

- `add_message(session_id, role, content) -> None` grava histórico bruto.
- `recent_messages(session_id, limit=12) -> list[dict]` devolve `{role, content}` na ordem cronológica.
- `context(query, session_id, token_budget=1200) -> list[dict]` devolve mensagens de contexto relevantes, limitadas ao orçamento.
- `consolidate(session_id) -> int` consolida somente fatos explicitamente duráveis/relevantes; duplicatas e fatos conflitantes devem ser tratados sem apagar o histórico bruto.
- `remember(content, kind="semantic") -> id`; `search(query, limit=5) -> list[dict]`; `update(memory_id, content) -> bool`; `delete(memory_id) -> bool`.

SQLite é o backend obrigatório. Embeddings e serviços externos não são exigidos. A integração continuará funcionando sem uma rotina de extração automática de fatos; consolidação precisa ser deliberada.

## WebSocket backend/frontend

Servidor local em `127.0.0.1:8765`, JSON UTF-8, uma mensagem por frame. Eventos do backend:

```json
{"type":"state","state":"idle|listening|thinking|speaking"}
{"type":"transcript","text":"..."}
{"type":"response","text":"..."}
{"type":"audio_level","value":0.0}
{"type":"error","message":"..."}
```

Comandos do frontend:

```json
{"type":"command","command":"start|stop|toggle"}
```

Microfone continua sendo capturado pelo backend Python. Frontend inicia/para o ciclo de escuta e apresenta eventos; não captura nem retransmite PCM.

## Fluxo de turno

Manter os modelos e o processamento existentes. O turno grava mensagem do usuário, consulta contexto limitado, chama Ollama, grava resposta, e sinaliza os estados reais. Histórico recente permanece disponível. Erros e encerramento devem fechar o servidor WebSocket e áudio.
