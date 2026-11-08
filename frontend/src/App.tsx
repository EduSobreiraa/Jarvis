import { Bell, Mic, MicOff, Radio, Trash2 } from 'lucide-react'
import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'

type State = 'idle' | 'listening' | 'thinking' | 'speaking'
type Reminder = { id: string; title: string; due_at: string }
type Event = { type: string; state?: State; text?: string; message?: string; items?: Reminder[]; item?: Reminder }

const labels: Record<State, string> = { idle: 'Pronto para ouvir', listening: 'Estou ouvindo', thinking: 'Um instante', speaking: 'Jarvis está falando' }

export default function App() {
  const [state, setState] = useState<State>('idle')
  const [demo, setDemo] = useState(new URLSearchParams(location.search).get('demo') === 'true')
  const [connected, setConnected] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [response, setResponse] = useState('')
  const [error, setError] = useState('')
  const [reminders, setReminders] = useState<Reminder[]>([])
  const [reminderTitle, setReminderTitle] = useState('')
  const [reminderDate, setReminderDate] = useState('')
  const [dueReminders, setDueReminders] = useState<Reminder[]>([])
  const socket = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (demo) { setConnected(false); return }
    let active = true
    let ws: WebSocket
    try { ws = new WebSocket('ws://127.0.0.1:8765'); socket.current = ws }
    catch { setError('Não foi possível conectar ao Jarvis.'); return }
    ws.onopen = () => { if (active) { setConnected(true); setError('') } }
    ws.onclose = () => { if (active) { setConnected(false); setState('idle') } }
    ws.onerror = () => { if (active) setError('Backend indisponível. Ative o modo demonstração ou inicie o Jarvis.') }
    ws.onmessage = (message) => {
      try {
        const event = JSON.parse(message.data) as Event
        if (event.type === 'state' && event.state) setState(event.state)
        if (event.type === 'transcript' && event.text) setTranscript(event.text)
        if (event.type === 'response' && event.text) setResponse(event.text)
        if (event.type === 'error') setError(event.message || 'Falha no Jarvis.')
        if (event.type === 'reminders' && event.items) setReminders(event.items)
        if (event.type === 'reminder_due' && event.item) setDueReminders((current) => [...current, event.item!])
      } catch { setError('Mensagem inválida recebida do backend.') }
    }
    return () => { active = false; ws.close(); socket.current = null }
  }, [demo])

  const command = useCallback(() => {
    if (demo) {
      setError('')
      setState((current) => {
        const order: State[] = ['idle', 'listening', 'thinking', 'speaking']
        const next = order[(order.indexOf(current) + 1) % order.length]
        if (next === 'listening') setTranscript('Conteúdo de demonstração')
        if (next === 'speaking') setResponse('Olá! A interface está funcionando no modo demonstração.')
        return next
      })
      return
    }
    if (socket.current?.readyState === WebSocket.OPEN) {
      const interrupt = state === 'speaking'
      const listening = state !== 'listening'
      socket.current.send(JSON.stringify({ type: 'command', command: interrupt ? 'interrupt' : listening ? 'start' : 'stop' }))
      setState(interrupt || listening ? 'listening' : 'idle')
    }
    else setError('Backend desconectado. Inicie o Jarvis e tente novamente.')
  }, [demo, state])

  const sendReminder = (event: FormEvent) => {
    event.preventDefault()
    if (!reminderTitle.trim() || !reminderDate || socket.current?.readyState !== WebSocket.OPEN) return
    socket.current.send(JSON.stringify({ type: 'command', command: 'reminder_add', title: reminderTitle, due_at: new Date(reminderDate).toISOString() }))
    setReminderTitle('')
    setReminderDate('')
  }

  const removeReminder = (id: string) => {
    socket.current?.send(JSON.stringify({ type: 'command', command: 'reminder_delete', id }))
  }

  return <main className="shell">
    <header className="topbar"><div className="wordmark"><span className="mark">J</span><span>JARVIS</span></div><button className={`mode ${demo ? 'demo' : ''}`} onClick={() => { setDemo(!demo); setError(''); setState('idle') }}><span className="connection-dot" />{demo ? 'Demonstração' : connected ? 'Conectado' : 'Conectando'}</button></header>
    <section className="stage" aria-label="Assistente Jarvis">
      <div className={`robot robot--${state}`} role="img" aria-label={`Robô Jarvis: ${labels[state].toLowerCase()}`} />
      <p className="status" aria-live="polite">{labels[state]}</p>
      <button className={`mic ${state === 'listening' ? 'active' : ''}`} onClick={command} aria-label={state === 'speaking' ? 'Interromper fala e ouvir' : state === 'listening' ? 'Parar de ouvir' : 'Iniciar escuta'} disabled={state === 'thinking'}>
        {state === 'listening' || state === 'speaking' ? <MicOff size={23} strokeWidth={1.8} /> : <Mic size={23} strokeWidth={1.8} />}
      </button>
      <p className="hint">{demo ? 'Toque no microfone para experimentar' : 'Toque no microfone para conversar'}</p>
      {(transcript || response) && <div className="caption" aria-live="polite">{transcript && <span>{transcript}</span>}{response && <strong>{response}</strong>}</div>}
      {error && <div className="error" role="status">{error}</div>}
      {dueReminders.length > 0 && <div className="reminder-alert" role="alert">{dueReminders.map((item) => <div key={item.id}><Bell size={16} /> <span>Lembrete: {item.title}</span><button onClick={() => setDueReminders((current) => current.filter((reminder) => reminder.id !== item.id))} aria-label={`Dispensar lembrete: ${item.title}`}>Dispensar</button></div>)}</div>}
      {!demo && <section className="reminders" aria-labelledby="reminders-title">
        <h2 id="reminders-title">Lembretes</h2>
        <form onSubmit={sendReminder}>
          <label>O que lembrar<input value={reminderTitle} onChange={(event) => setReminderTitle(event.target.value)} maxLength={200} required /></label>
          <label>Data e hora<input type="datetime-local" value={reminderDate} onChange={(event) => setReminderDate(event.target.value)} min={new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16)} required /></label>
          <button type="submit" disabled={!connected}>Adicionar</button>
        </form>
        {reminders.length === 0 ? <p className="empty-reminders">Nenhum lembrete agendado.</p> : <ul>{reminders.map((item) => <li key={item.id}><span>{item.title}<time dateTime={item.due_at}>{new Date(item.due_at).toLocaleString('pt-BR')}</time></span><button onClick={() => removeReminder(item.id)} aria-label={`Remover lembrete: ${item.title}`}><Trash2 size={15} /></button></li>)}</ul>}
      </section>}
    </section>
    <footer className="footer"><span><Radio size={14} /> Processamento local</span></footer>
  </main>
}
