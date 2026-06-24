import { useState } from 'react'
import { startRun } from '../api'

export default function NewRunModal({ onClose, onCreated }) {
  const [issueKey, setIssueKey] = useState('')
  const [summary, setSummary] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!issueKey.trim()) return
    setLoading(true)
    setError('')
    try {
      const { run_id } = await startRun(issueKey.trim().toUpperCase(), summary.trim())
      onCreated(run_id)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-slate-900 border border-slate-700 rounded-lg w-full max-w-md mx-4 shadow-2xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
          <h2 className="text-sm font-semibold text-slate-200">Start New Run</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300 text-lg leading-none">×</button>
        </div>

        <form onSubmit={handleSubmit} className="px-5 py-5 space-y-4">
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 tracking-wide">
              Jira Issue Key <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={issueKey}
              onChange={e => setIssueKey(e.target.value)}
              placeholder="e.g. PROJ-456"
              autoFocus
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1.5 tracking-wide">
              Summary <span className="text-slate-600">(optional)</span>
            </label>
            <input
              type="text"
              value={summary}
              onChange={e => setSummary(e.target.value)}
              placeholder="Short description of the bug"
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-900/20 border border-red-500/20 rounded px-3 py-2">
              {error}
            </p>
          )}

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 text-sm text-slate-400 border border-slate-700 rounded hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!issueKey.trim() || loading}
              className="flex-1 py-2 text-sm font-mono text-blue-400 bg-blue-500/10 border border-blue-500/30 rounded hover:bg-blue-500/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Starting…' : 'Run Pipeline'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
