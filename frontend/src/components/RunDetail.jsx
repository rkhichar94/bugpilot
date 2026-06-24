import { useState, useEffect } from 'react'
import PipelineStages from './PipelineStages'
import LogStream from './LogStream'
import DiffViewer from './DiffViewer'
import { fetchRun, approveRun, rejectRun } from '../api'

const RUNNING = new Set(['PENDING','CLONING','ANALYZING','FIXING','TESTING','CREATING_PR'])

const STATUS_BADGE = {
  PENDING:           'bg-slate-700 text-slate-300',
  CLONING:           'bg-blue-500/15 text-blue-400 border border-blue-500/30',
  ANALYZING:         'bg-blue-500/15 text-blue-400 border border-blue-500/30',
  FIXING:            'bg-blue-500/15 text-blue-400 border border-blue-500/30',
  TESTING:           'bg-blue-500/15 text-blue-400 border border-blue-500/30',
  CREATING_PR:       'bg-blue-500/15 text-blue-400 border border-blue-500/30',
  AWAITING_APPROVAL: 'bg-amber-500/15 text-amber-400 border border-amber-500/30',
  APPROVED:          'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
  REJECTED:          'bg-slate-700 text-slate-400',
  FAILED:            'bg-red-500/15 text-red-400 border border-red-500/30',
}

const STATUS_LABEL = {
  PENDING:           'Pending',
  CLONING:           'Cloning…',
  ANALYZING:         'Analyzing…',
  FIXING:            'Generating fix…',
  TESTING:           'Running tests…',
  CREATING_PR:       'Opening PR…',
  AWAITING_APPROVAL: 'Awaiting Review',
  APPROVED:          'Approved',
  REJECTED:          'Rejected',
  FAILED:            'Failed',
}

export default function RunDetail({ runId }) {
  const [run, setRun] = useState(null)
  const [tab, setTab] = useState('logs')
  const [actionDone, setActionDone] = useState(false)

  useEffect(() => {
    const refresh = () => fetchRun(runId).then(setRun).catch(() => {})
    refresh()
    const t = setInterval(refresh, 2000)
    return () => clearInterval(t)
  }, [runId])

  if (!run) {
    return (
      <div className="flex-1 flex items-center justify-center text-slate-600 text-sm">
        Loading…
      </div>
    )
  }

  const isRunning = RUNNING.has(run.status)
  const isDone = !isRunning
  const canAct = run.status === 'AWAITING_APPROVAL' && !actionDone

  const handleApprove = async () => {
    await approveRun(runId)
    setActionDone(true)
    setRun(r => ({ ...r, status: 'APPROVED' }))
  }

  const handleReject = async () => {
    await rejectRun(runId)
    setActionDone(true)
    setRun(r => ({ ...r, status: 'REJECTED' }))
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden min-w-0">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800 flex-shrink-0">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="font-mono font-bold text-white text-sm">{run.issue_key}</span>
              {run.summary && (
                <span className="text-slate-400 text-sm truncate max-w-md">{run.summary}</span>
              )}
            </div>
            <div className="text-xs text-slate-600 mt-0.5" style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>
              run/{run.id}
            </div>
          </div>
          <span className={`flex-shrink-0 text-xs px-2 py-1 rounded font-mono ${STATUS_BADGE[run.status] ?? 'bg-slate-700 text-slate-300'}`}>
            {STATUS_LABEL[run.status] ?? run.status}
          </span>
        </div>

        <div className="mt-4">
          <PipelineStages status={run.status} stage={run.stage} />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 px-6 flex-shrink-0">
        {['logs', 'diff'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-xs font-mono capitalize transition-colors -mb-px border-b-2 ${
              tab === t
                ? 'text-blue-400 border-blue-500'
                : 'text-slate-500 border-transparent hover:text-slate-300'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden bg-slate-950">
        {tab === 'logs' && <LogStream runId={runId} done={isDone} />}
        {tab === 'diff' && <DiffViewer runId={runId} />}
      </div>

      {/* PR bar */}
      {(canAct || run.status === 'APPROVED' || run.status === 'REJECTED') && (
        <div className="border-t border-slate-800 px-6 py-3 flex items-center gap-3 flex-shrink-0 bg-slate-900">
          {run.pr_url && (
            <a
              href={run.pr_url}
              target="_blank"
              rel="noreferrer"
              className="text-xs font-mono text-blue-400 hover:text-blue-300 underline underline-offset-2 truncate flex-1 min-w-0"
            >
              {run.pr_url}
            </a>
          )}

          {canAct && (
            <div className="flex gap-2 flex-shrink-0">
              <button
                onClick={handleApprove}
                className="px-4 py-1.5 text-xs font-mono bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded hover:bg-emerald-500/20 transition-colors"
              >
                ✓ Approve
              </button>
              <button
                onClick={handleReject}
                className="px-4 py-1.5 text-xs font-mono bg-red-500/10 border border-red-500/30 text-red-400 rounded hover:bg-red-500/20 transition-colors"
              >
                ✗ Reject
              </button>
            </div>
          )}

          {run.status === 'APPROVED' && !canAct && (
            <span className="text-xs font-mono text-emerald-400">✓ Approved</span>
          )}
          {run.status === 'REJECTED' && !canAct && (
            <span className="text-xs font-mono text-slate-500">✗ Rejected</span>
          )}
        </div>
      )}

      {run.status === 'FAILED' && run.error && (
        <div className="border-t border-slate-800 px-6 py-3 flex-shrink-0 bg-red-950/20">
          <p className="text-xs font-mono text-red-400">{run.error}</p>
        </div>
      )}
    </div>
  )
}
