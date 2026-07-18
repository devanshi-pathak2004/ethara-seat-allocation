import { useState, useRef, useEffect } from 'react'
import { Sparkles, Send, Bot, User } from 'lucide-react'
import { api } from '../lib/api'

const SUGGESTIONS = [
  'Where is my seat? My email is amit@ethara.ai',
  'Which project is amit@ethara.ai assigned to?',
  'Show all available seats on Floor 3',
  'Who is sitting near amit@ethara.ai?',
  'How many seats are occupied for Project Indigo?',
]

export default function Assistant() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: "Hi! I'm the Ethara seating assistant. Ask me where someone sits, which project they're on, available seats on a floor, or team utilization.",
    },
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, busy])

  const send = async (text) => {
    const q = (text ?? input).trim()
    if (!q || busy) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', text: q }])
    setBusy(true)
    try {
      const res = await api.aiQuery(q)
      setMessages((m) => [...m, { role: 'assistant', text: res.answer, intent: res.intent }])
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', text: `Sorry, something went wrong: ${e.message}`, error: true }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-8rem)] max-w-3xl flex-col">
      <header className="mb-4">
        <h1 className="flex items-center gap-2 text-2xl font-extrabold tracking-tight text-slate-800">
          <Sparkles className="text-brand-500" /> AI Assistant
        </h1>
        <p className="text-sm text-slate-500">
          Natural-language queries for seats, projects & utilization.
        </p>
      </header>

      <div className="card flex flex-1 flex-col overflow-hidden">
        <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-5">
          {messages.map((m, i) => (
            <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-full ${m.role === 'user' ? 'bg-slate-200 text-slate-600' : 'bg-gradient-to-br from-brand-500 to-brand-700 text-white'}`}>
                {m.role === 'user' ? <User size={17} /> : <Bot size={17} />}
              </div>
              <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                m.role === 'user'
                  ? 'bg-brand-600 text-white'
                  : m.error
                    ? 'bg-rose-50 text-rose-700'
                    : 'bg-slate-100 text-slate-700'
              }`}>
                {m.text}
                {m.intent && m.intent !== 'unknown' && (
                  <span className="mt-1.5 block text-[10px] uppercase tracking-wide opacity-50">
                    intent · {m.intent}
                  </span>
                )}
              </div>
            </div>
          ))}
          {busy && (
            <div className="flex gap-3">
              <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gradient-to-br from-brand-500 to-brand-700 text-white">
                <Bot size={17} />
              </div>
              <div className="flex items-center gap-1 rounded-2xl bg-slate-100 px-4 py-3">
                {[0, 1, 2].map((d) => (
                  <span key={d} className="h-2 w-2 animate-bounce rounded-full bg-slate-400" style={{ animationDelay: `${d * 0.15}s` }} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Suggestions */}
        <div className="border-t border-slate-100 px-5 pt-3">
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                disabled={busy}
                className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-brand-300 hover:bg-brand-50 hover:text-brand-700 disabled:opacity-50"
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Input */}
        <form
          onSubmit={(e) => { e.preventDefault(); send() }}
          className="flex items-center gap-2 p-4"
        >
          <input
            className="input"
            placeholder="Ask about seats, projects, availability…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button type="submit" className="btn-primary shrink-0" disabled={busy || !input.trim()}>
            <Send size={16} /> Send
          </button>
        </form>
      </div>
    </div>
  )
}
