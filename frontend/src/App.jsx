import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import RunDetail from './components/RunDetail'
import NewRunModal from './components/NewRunModal'
import { fetchRuns } from './api'

export default function App() {
  const [runs, setRuns] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    const refresh = () => fetchRuns().then(setRuns).catch(() => {})
    refresh()
    const t = setInterval(refresh, 3000)
    return () => clearInterval(t)
  }, [])

  const handleCreated = (id) => {
    setSelectedId(id)
    setShowModal(false)
  }

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-200" style={{ fontFamily: 'ui-sans-serif, system-ui, -apple-system, sans-serif' }}>
      <header className="flex items-center justify-between px-6 py-3 border-b border-slate-800 flex-shrink-0">
        <div className="flex items-baseline gap-3">
          <span className="text-blue-400 font-bold tracking-widest text-sm" style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>
            BUGPILOT
          </span>
          <span className="text-slate-500 text-xs">Autonomous Bug Resolution Pipeline</span>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded hover:bg-blue-500/20 transition-colors"
          style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}
        >
          + New Run
        </button>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <Sidebar runs={runs} selectedId={selectedId} onSelect={setSelectedId} onNew={() => setShowModal(true)} />
        {selectedId
          ? <RunDetail key={selectedId} runId={selectedId} />
          : <EmptyState onNew={() => setShowModal(true)} />
        }
      </div>

      {showModal && (
        <NewRunModal onClose={() => setShowModal(false)} onCreated={handleCreated} />
      )}
    </div>
  )
}

function EmptyState({ onNew }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-3 text-slate-500">
      <div className="text-5xl opacity-10">◈</div>
      <p className="text-sm">No run selected</p>
      <button onClick={onNew} className="text-xs text-blue-400 hover:text-blue-300 underline underline-offset-2">
        Start a new run
      </button>
    </div>
  )
}
