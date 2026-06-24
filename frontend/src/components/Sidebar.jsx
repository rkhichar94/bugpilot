import { formatDistanceToNow } from '../utils'

const STATUS_DOT = {
  PENDING:           'bg-slate-600',
  CLONING:           'bg-blue-400 animate-pulse',
  ANALYZING:         'bg-blue-400 animate-pulse',
  FIXING:            'bg-blue-400 animate-pulse',
  TESTING:           'bg-blue-400 animate-pulse',
  CREATING_PR:       'bg-blue-400 animate-pulse',
  AWAITING_APPROVAL: 'bg-amber-400',
  APPROVED:          'bg-emerald-400',
  REJECTED:          'bg-slate-500',
  FAILED:            'bg-red-400',
}

const STATUS_TEXT = {
  PENDING:           'text-slate-500',
  CLONING:           'text-blue-400',
  ANALYZING:         'text-blue-400',
  FIXING:            'text-blue-400',
  TESTING:           'text-blue-400',
  CREATING_PR:       'text-blue-400',
  AWAITING_APPROVAL: 'text-amber-400',
  APPROVED:          'text-emerald-400',
  REJECTED:          'text-slate-500',
  FAILED:            'text-red-400',
}

const STATUS_LABEL = {
  PENDING:           'Pending',
  CLONING:           'Cloning…',
  ANALYZING:         'Analyzing…',
  FIXING:            'Fixing…',
  TESTING:           'Testing…',
  CREATING_PR:       'Opening PR…',
  AWAITING_APPROVAL: 'Awaiting Review',
  APPROVED:          'Approved',
  REJECTED:          'Rejected',
  FAILED:            'Failed',
}

export default function Sidebar({ runs, selectedId, onSelect, onNew }) {
  return (
    <aside className="w-64 flex-shrink-0 border-r border-slate-800 bg-slate-900 flex flex-col">
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <span className="text-xs text-slate-400 font-medium tracking-wider uppercase">Runs</span>
        <span className="text-xs text-slate-600">{runs.length}</span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {runs.length === 0 && (
          <div className="px-4 py-8 text-center text-xs text-slate-600">
            No runs yet
          </div>
        )}
        {runs.map(run => (
          <button
            key={run.id}
            onClick={() => onSelect(run.id)}
            className={`w-full text-left px-4 py-3 border-b border-slate-800/50 hover:bg-slate-800/50 transition-colors ${
              selectedId === run.id ? 'bg-slate-800' : ''
            }`}
          >
            <div className="flex items-center gap-2 mb-0.5">
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${STATUS_DOT[run.status] ?? 'bg-slate-600'}`} />
              <span className="font-mono text-xs font-semibold text-slate-200 truncate">
                {run.issue_key}
              </span>
            </div>
            <div className={`text-xs pl-4 ${STATUS_TEXT[run.status] ?? 'text-slate-500'}`}>
              {STATUS_LABEL[run.status] ?? run.status}
            </div>
            <div className="text-xs pl-4 text-slate-600 mt-0.5">
              {formatDistanceToNow(run.created_at)}
            </div>
          </button>
        ))}
      </div>

      <div className="p-3 border-t border-slate-800">
        <button
          onClick={onNew}
          className="w-full py-2 text-xs font-mono text-blue-400 bg-blue-500/10 border border-blue-500/20 rounded hover:bg-blue-500/20 transition-colors"
        >
          + New Run
        </button>
      </div>
    </aside>
  )
}
