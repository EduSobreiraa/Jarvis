# Spec: tarefas agendadas

## Processo obrigatório de desenvolvimento

Toda feature segue este fluxo:

1. **Planejamento:** registrar objetivo, escopo, critérios de aceite e riscos nesta spec ou em uma spec própria antes de implementar.
2. **Implementação:** construir o escopo aprovado e manter o estado da spec atualizado enquanto o trabalho avança.
3. **Validação:** executar QA e os testes relevantes. A validação só passa quando todos os resultados esperados forem aprovados; registrar aqui os comandos e resultados.
4. **Documentação:** atualizar a spec com o comportamento entregue, decisões e limitações observadas.
5. **Aprovação:** revisar a implementação e a documentação. A feature só pode ser marcada como **Completa** depois de documentada, validada e aprovada.

Até que uma etapa seja concluída, seu estado deve permanecer **Pendente** ou **Em andamento**; não antecipar aprovação nem conclusão.

### Papéis de trabalho

- **Agente principal:** orquestra o trabalho entre as etapas e comunica o status e bloqueios.
- **Subagente de implementação:** implementa o escopo aprovado.
- **Subagente de QA/validação:** verifica os critérios de aceite e executa os testes relevantes; reporta resultados sem aprovar etapas que falharam.
- **Subagente documental:** mantém esta spec e as demais specs atualizadas com decisões, estado e resultados registrados.
- Os três subagentes (implementação, QA/validação e documentação) usam **gpt-6-luna** com raciocínio **high**.

Os papéis não alteram o fluxo de conclusão: implementação e documentação só podem ser marcadas como concluídas após o registro de QA aprovado; a aprovação final depende da revisão do agente principal.

## Estado desta feature

| Etapa | Estado | Registro |
|---|---|---|
| Planejamento | Concluído | Escopo inicial e critérios abaixo. |
| Implementação | Em andamento | Reaberta após falha runtime: lembrete persistido pela UI não gera alerta nem atualiza `notified_at`. |
| QA e testes | Em andamento | Teste manual via UI falhou; repetir após correção. Testes automatizados e smoke SQLite anteriores passaram. |
| Documentação final | Em andamento | Spec reaberta para registrar a falha runtime e atualizar QA após o fix. |
| Aprovação | Pendente | Aguarda correção, QA runtime aprovado e revisão final. |

**Estado geral: Pendente.** A integração SQLite foi corrigida, mas o alerta runtime da UI falhou; não considerar completa até o fix, nova validação e aprovação.

## Objetivo

Permitir que o Jarvis crie lembretes para uma data e hora futuras e avise o usuário quando chegar o horário.

## Escopo inicial

- Agendar e apresentar **lembretes** ao usuário.
- Persistir lembretes para que não desapareçam ao encerrar e reiniciar o Jarvis.
- Incluir informação suficiente para identificar o lembrete e o horário agendado.
- Permitir consultar e cancelar lembretes pendentes, se necessário para cumprir o fluxo de lembrete.
- Ao vencer, notificar o usuário sem executar ações externas ou arbitrárias.

## Fora do escopo inicial

- Executar comandos, alterar arquivos, enviar mensagens ou realizar qualquer ação além de avisar sobre um lembrete.
- Agendamentos recorrentes, integrações com calendários ou sincronização em nuvem.
- Busca na web, automação/controle do computador e execução de plugins.

Essas capacidades exigem especificações próprias, revisão de riscos e critérios de aceite antes de qualquer implementação. Criar specs separadas para **web search**, **computer use**, **plugins** e outras capacidades futuras; não ampliar esta spec para incorporá-las.

## Critérios de aceite

- O usuário consegue criar um lembrete com descrição e horário compreensíveis.
- O lembrete continua disponível depois de reiniciar o Jarvis.
- O usuário consegue identificar e cancelar um lembrete ainda pendente.
- Quando chega o horário, o Jarvis avisa o usuário e não executa a ação descrita como se fosse uma autorização para agir.
- Novos lembretes só podem ser criados para horários futuros; entradas com horário passado devem ser recusadas ou esclarecidas.
- Lembretes que vencerem enquanto o Jarvis estiver fechado devem continuar disponíveis e ser avisados quando o backend voltar a rodar e a UI local se reconectar.
- Entradas inválidas ou ambíguas são tratadas com segurança: o Jarvis pede esclarecimento ou informa que não conseguiu agendar.
- Testes cobrem criação, persistência, vencimento, cancelamento e entradas inválidas.

## Decisões e limites

- A capacidade é restrita a lembretes; texto do lembrete é conteúdo para exibição, não uma instrução executável.
- A notificação é visual na UI local. O backend precisa estar rodando e a UI precisa estar conectada para recebê-la.
- A entrega é **at-most-once**: se a conexão WebSocket cair exatamente durante a entrega, o aviso pode não ser repetido. Lembretes vencidos durante o período fechado devem, ainda assim, ser detectados e avisados quando houver reconexão.
- O campo `datetime-local` interpreta o horário no fuso local do navegador; o backend normaliza e persiste o instante em UTC.
- Se qualquer critério mudar, atualizar esta spec antes de ampliar o escopo implementado.

## Registro de validação e aprovação

### Incidente de integração SQLite

- **Falha observada:** `MemoryStore` usado junto com `ReminderStore` bloqueava o SQLite e impedia a criação da tabela de lembretes.
- **Estado:** correção implementada; smoke test pós-fix com ambos os stores passou.
- **Impacto nos dados:** dois lembretes anteriores não foram persistidos.
- **Uso atual:** o usuário precisa reabrir o app pela interface GUI para usar lembretes.

### Validação após o fix

- `.venv/bin/python -m unittest discover -s tests -v`: **16/16 passaram**.
- `cd frontend && npm run build`: **passou**.
- Smoke test em SQLite temporário com `MemoryStore` e `ReminderStore`: **passou**.
- Tentativa de `./scripts/start-jarvis.sh`: falhou no ambiente headless com `ImportError: [metal::load_device] No Metal device available`; o backend não iniciou e não houve listener na porta 8765.
- Limite desta validação: os testes automatizados e o smoke SQLite não cobrem entrega runtime do alerta na UI.
- Risco conhecido: entrega **at-most-once**; uma queda do WebSocket exatamente durante a entrega pode fazer o aviso visual não se repetir.
- Resultado dos testes automatizados e do smoke SQLite: **Aprovado**.
- Resultado da validação runtime WebSocket/UI: **Falhou** no teste manual descrito abaixo; correção e novo QA pendentes.
- Revisão/aprovação final: **Pendente**.
- Data e responsável pelo QA: **2026-11-07 / QA**.

### Falha runtime: alerta não entregue pela UI

- **Reprodução:** criar pela UI um lembrete para **19:54 no horário local**.
- **Resultado observado:** o lembrete foi gravado no SQLite, mas não gerou alerta e `notified_at` permaneceu `NULL`.
- **Após recarregar a UI:** o banner também não foi exibido.
- **Resultado esperado:** ao vencer, o lembrete deve ser marcado como notificado e o alerta visual deve aparecer na UI; a entrega após recarga deve respeitar o comportamento documentado de lembretes vencidos.
- **Estado:** falha reproduzida; implementação e QA em andamento, aguardando fix e nova validação runtime.
