const STAGES = [
  { id: 'clone_repo',    label: 'Clone',   num: '01' },
  { id: 'issue_analyst', label: 'Analyze', num: '02' },
  { id: 'fix_generator', label: 'Fix',     num: '03' },
  { id: 'test_runner',   label: 'Test',    num: '04' },
  { id: 'pr_creator',    label: 'PR',      num: '05' },
]

const STATUS_TO_ACTIVE = {
  CLONING:           0,
  ANALYZING:         1,
  FIXING:            2,
  TESTING:           3,
  CREATING_PR:       4,
  AWAITING_APPROVAL: 5,
  APPROVED:          5,
  REJECTED:          5,
  FAILED:            -1,
}

export default function PipelineStages({ status, stage }) {
  const activeIdx = STATUS_TO_ACTIVE[status] ?? -1
  const failed = status === 'FAILED'

  const failedIdx = failed
    ? STAGES.findIndex(s => s.id === stage)
    : -1

  return (
    <div className="flex items-center gap-0">
      {STAGES.map((s, i) => {
        const done = activeIdx > i || (activeIdx === 5 && !failed)
        const active = activeIdx === i && !failed
        const isFailed = failedIdx === i
        const pending = !done && !active && !isFailed

        return (
          <div key={s.id} className="flex items-center">
            {/* Node */}
            <div className="flex flex-col items-center gap-1">
              <div className={`
                w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-mono font-bold
                transition-all duration-300
                ${done    ? 'border-emerald-500 bg-emerald-500/10 text-emerald-400' : ''}
                ${active  ? 'border-blue-400 bg-blue-400/10 text-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.4)]' : ''}
                ${isFailed ? 'border-red-500 bg-red-500/10 text-red-400' : ''}
                ${pending ? 'border-slate-700 bg-slate-800/50 text-slate-600' : ''}
              `}>
                {done ? '✓' : active ? <span className="animate-pulse">●</span> : isFailed ? '✗' : s.num}
              </div>
              <span className={`text-xs leading-none ${
                done ? 'text-emerald-500' :
                active ? 'text-blue-400' :
                isFailed ? 'text-red-400' :
                'text-slate-600'
              }`}>
                {s.label}
              </span>
            </div>

            {/* Connector */}
            {i < STAGES.length - 1 && (
              <div className={`h-px w-8 mb-4 transition-colors duration-300 ${
                done ? 'bg-emerald-500/40' : 'bg-slate-700'
              }`} />
            )}
          </div>
        )
      })}
    </div>
  )
}
