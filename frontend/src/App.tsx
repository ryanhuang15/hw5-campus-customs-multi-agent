import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  ArrowUpRight,
  Check,
  CheckCircle2,
  CircleDot,
  Clock3,
  DollarSign,
  Landmark,
  LoaderCircle,
  MessageSquareText,
  PackageSearch,
  RefreshCw,
  Send,
  ShieldCheck,
  Sparkles,
  Store,
  Users,
  WalletCards,
} from 'lucide-react'

const API_BASE = 'http://localhost:8000'

type Ticket = {
  id: number
  type: string
  requester: string
  subject: string
  status: string
  is_open: boolean
  is_resolved: boolean
}

type Event = {
  timestamp: string
  ticket_id: number | null
  task?: string | null
  agent: string
  action: string
  called?: string | null
  result: string
  continuation_reason: string
}

type ApprovalRequest = {
  kind: 'invoice' | 'lease'
  ref_id: number
  amount: number
  reason: string
}

type AgentReply = {
  status: string
  summary: string
  facts_used: string[]
  next_action?: string | null
  delegated_to: string[]
  approval_request?: ApprovalRequest | null
}

type RunResponse = {
  ticket_id: number
  result: AgentReply
  recent_events: Event[]
}

type Cash = { account: string; balance: number; date: string }

const agentMeta: Record<string, { color: string; icon: typeof Users; label: string }> = {
  Boss: { color: 'boss', icon: Sparkles, label: 'Orchestrator' },
  Inventory: { color: 'inventory', icon: PackageSearch, label: 'Stock & supply' },
  Accounting: { color: 'accounting', icon: WalletCards, label: 'Finance control' },
  Facilities: { color: 'facilities', icon: Store, label: 'Shop & lease' },
  'Customer Service': { color: 'customer', icon: MessageSquareText, label: 'Draft communications' },
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail ?? `Backend request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

function formatTime(timestamp: string) {
  return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function money(value: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

function agentClass(agent: string) {
  return agentMeta[agent]?.color ?? 'unknown'
}

function App() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [events, setEvents] = useState<Event[]>([])
  const [cash, setCash] = useState<Cash | null>(null)
  const [run, setRun] = useState<RunResponse | null>(null)
  const [running, setRunning] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [approver, setApprover] = useState('')
  const [approvalReference, setApprovalReference] = useState('human-approved:')
  const [approving, setApproving] = useState(false)

  const selectedTicket = tickets.find((ticket) => ticket.id === selectedId) ?? null
  const ticketEvents = useMemo(() => events.filter((event) => event.ticket_id === selectedId), [events, selectedId])
  const participatingAgents = useMemo(() => {
    const names = new Set(ticketEvents.map((event) => event.agent))
    if (run?.ticket_id === selectedId) names.add('Boss')
    return [...names]
  }, [ticketEvents, run, selectedId])

  const loadTickets = useCallback(async () => {
    const response = await api<{ tickets: Ticket[] }>('/api/tickets')
    setTickets(response.tickets)
    setSelectedId((current) => current ?? response.tickets[0]?.id ?? null)
  }, [])

  const loadEvents = useCallback(async () => {
    const response = await api<{ events: Event[] }>('/api/events?limit=100')
    setEvents(response.events)
  }, [])

  const loadCash = useCallback(async () => {
    setCash(await api<Cash>('/api/cash'))
  }, [])

  const refresh = useCallback(async () => {
    setError('')
    try {
      await Promise.all([loadTickets(), loadEvents(), loadCash()])
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not reach the FastAPI backend.')
    } finally {
      setLoading(false)
    }
  }, [loadCash, loadEvents, loadTickets])

  useEffect(() => { void refresh() }, [refresh])

  useEffect(() => {
    if (!running) return
    const interval = window.setInterval(() => { void loadEvents() }, 1200)
    return () => window.clearInterval(interval)
  }, [running, loadEvents])

  async function startRun() {
    if (!selectedId || running) return
    setError('')
    setRun(null)
    setRunning(true)
    try {
      const response = await api<RunResponse>(`/api/tickets/${selectedId}/run`, { method: 'POST' })
      setRun(response)
      setEvents(response.recent_events)
      await Promise.all([loadTickets(), loadCash()])
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The agent run could not be started.')
    } finally {
      setRunning(false)
      await loadEvents()
    }
  }

  async function approvePayment() {
    const request = run?.result.approval_request
    if (!request || !approver.trim() || !approvalReference.startsWith('human-approved:')) return
    setApproving(true)
    setError('')
    try {
      await api('/api/approvals/payment', {
        method: 'POST',
        body: JSON.stringify({ ...request, approved_by: approver.trim(), approval_reference: approvalReference.trim() }),
      })
      setRun((current) => current ? { ...current, result: { ...current.result, approval_request: null } } : current)
      setApprover('')
      setApprovalReference('human-approved:')
      await Promise.all([loadCash(), loadTickets(), loadEvents()])
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The approval could not be completed.')
    } finally {
      setApproving(false)
    }
  }

  const summary = run?.ticket_id === selectedId ? run.result : null

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">CC</div><div><strong>Campus Customs</strong><span>Agent operations desk</span></div></div>
        <div className="side-label">Live workspace</div>
        <div className="side-status"><span className="live-dot" /> MCP + FastAPI connected</div>
        <div className="side-note"><ShieldCheck size={16} /> Humans remain the final authority for money.</div>
        <div className="sidebar-bottom"><span>YALE · MGT 409</span><span>v0.1 / local desk</span></div>
      </aside>

      <main className="main-content">
        <header className="topbar"><div><div className="kicker">Tuesday, August 31 · manager view</div><h1>Good morning, operator.</h1><p>Watch the team turn open requests into decisions.</p></div><button className="icon-button" onClick={() => void refresh()} title="Refresh dashboard"><RefreshCw size={18} /></button></header>

        {error && <div className="error-banner"><AlertTriangle size={18} /> {error}</div>}

        <section className="metrics">
          <div className="metric cash-metric"><div className="metric-icon"><DollarSign size={19} /></div><div><span>Checking balance</span><strong>{cash ? money(cash.balance) : '—'}</strong><small>{cash ? `As of ${cash.date}` : 'Loading from backend'}</small></div></div>
          <div className="metric"><div className="metric-icon dark"><CircleDot size={19} /></div><div><span>Open tickets</span><strong>{tickets.filter((ticket) => ticket.is_open).length} <em>/ {tickets.length || '—'}</em></strong><small>Live database status</small></div></div>
          <div className="metric"><div className="metric-icon dark"><Users size={19} /></div><div><span>Agent seats</span><strong>5</strong><small>Fully connected team</small></div></div>
        </section>

        <div className="workspace-grid">
          <section className="ticket-column panel-card"><div className="section-heading"><div><span className="kicker">Work queue</span><h2>Ticket board</h2></div><span className="live-pill"><span className="live-dot" /> Live</span></div>
            <div className="ticket-list">
              {loading ? <div className="empty-state">Loading tickets from the working database…</div> : tickets.map((ticket) => <button key={ticket.id} className={`ticket-row ${selectedId === ticket.id ? 'selected' : ''}`} onClick={() => { setSelectedId(ticket.id); setRun(null) }}>
                <div className={`ticket-number ${ticket.is_resolved ? 'resolved' : ''}`}>{ticket.id}</div><div className="ticket-copy"><div className="ticket-top"><span className="ticket-type">{ticket.type.replace('_', ' ')}</span><span className={`status ${ticket.is_resolved ? 'resolved' : 'open'}`}><span />{ticket.status}</span></div><strong>{ticket.subject}</strong><small>{ticket.requester}</small></div><ArrowUpRight size={17} className="arrow" />
              </button>)}
            </div>
          </section>

          <section className="detail-column panel-card"><div className="section-heading"><div><span className="kicker">Selected request</span><h2>{selectedTicket ? `Ticket ${selectedTicket.id}` : 'Select a ticket'}</h2></div>{selectedTicket && <span className={`status large ${selectedTicket.is_resolved ? 'resolved' : 'open'}`}><span />{selectedTicket.status}</span>}</div>
            {selectedTicket ? <><div className="ticket-hero"><div><span className="ticket-type">{selectedTicket.type.replace('_', ' ')}</span><h3>{selectedTicket.subject}</h3><p>Requested by <strong>{selectedTicket.requester}</strong></p></div><div className="hero-id">#{selectedTicket.id}</div></div><div className="run-controls"><button className="run-button" onClick={() => void startRun()} disabled={running || selectedTicket.is_resolved}>{running ? <><LoaderCircle className="spin" size={18} /> Team is working…</> : <><Sparkles size={18} /> Start agent team</>}</button><span>{selectedTicket.is_resolved ? 'Resolved in the working database' : 'Selecting a ticket never starts a run'}</span></div></> : <div className="empty-state">Choose a ticket from the board to inspect it.</div>}
          </section>
        </div>

        <section className="activity-layout">
          <div className="activity-panel panel-card"><div className="section-heading"><div><span className="kicker">Operational feed</span><h2>Agent activity</h2></div>{running && <span className="working-badge"><LoaderCircle className="spin" size={14} /> Running</span>}</div>
            <div className="agent-strip">{Object.entries(agentMeta).map(([name, meta]) => { const Icon = meta.icon; const active = participatingAgents.includes(name); return <div className={`agent-chip ${active ? 'active' : ''}`} key={name}><span className={`agent-avatar ${meta.color}`}><Icon size={15} /></span><span><strong>{name}</strong><small>{meta.label}</small></span>{active && <span className="active-bar" />}</div> })}</div>
            <div className="event-feed">{ticketEvents.length === 0 ? <div className="empty-state feed-empty"><MessageSquareText size={23} /><span>Activity for the selected ticket will appear here after you start its team.</span></div> : ticketEvents.slice().reverse().map((event, index) => { const EventIcon = agentMeta[event.agent]?.icon ?? CircleDot; return <div className="event" key={`${event.timestamp}-${index}`}><span className={`event-avatar ${agentClass(event.agent)}`}><EventIcon size={16} /></span><div className="event-body"><div className="event-line"><strong>{event.agent}</strong><span className="event-action">{event.action.replace('_', ' ')}</span><time>{formatTime(event.timestamp)}</time></div><p>{event.result}</p>{event.called && <code>{event.called}</code>}<small>{event.continuation_reason}</small></div></div> })}</div>
          </div>
          <aside className="side-column">
            <div className="summary-card panel-card"><div className="section-heading"><div><span className="kicker">Run readout</span><h2>What changed</h2></div><CheckCircle2 size={19} className="accent-icon" /></div>{summary ? <><div className="summary-status"><span className={`summary-dot ${summary.status}`} />{summary.status.replace('_', ' ')}</div><p>{summary.summary}</p>{summary.next_action && <div className="next-action"><span>Next action</span>{summary.next_action}</div>} {summary.facts_used.length > 0 && <div className="fact-list"><span>Facts used</span>{summary.facts_used.slice(0, 4).map((fact) => <div key={fact}><Check size={13} />{fact}</div>)}</div>}</> : <div className="empty-state">A concise agent readout will land here when a run finishes.</div>}</div>
            {summary?.approval_request && <div className="approval-card panel-card"><div className="approval-title"><div className="approval-icon"><ShieldCheck size={19} /></div><div><span className="kicker">Human decision required</span><h2>Approve payment</h2></div></div><p>{summary.approval_request.reason}</p><div className="approval-amount">{money(summary.approval_request.amount)} <small>{summary.approval_request.kind} #{summary.approval_request.ref_id}</small></div><label>Your name<input value={approver} onChange={(event) => setApprover(event.target.value)} placeholder="Human approver" /></label><label>Approval reference<input value={approvalReference} onChange={(event) => setApprovalReference(event.target.value)} /></label><button className="approve-button" disabled={approving || !approver.trim() || !approvalReference.startsWith('human-approved:')} onClick={() => void approvePayment()}>{approving ? <LoaderCircle className="spin" size={17} /> : <Check size={17} />} Approve and execute</button><small className="approval-warning">This is the only interface action that can authorize a payment.</small></div>}
          </aside>
        </section>
        <footer className="main-footer"><span><Landmark size={14} /> All facts shown here come from FastAPI → MCP → working database.</span><span>Local operations desk</span></footer>
      </main>
    </div>
  )
}

export default App
