import { useState, useEffect } from 'react'
import { fetchDiff } from '../api'

function DiffLine({ line }) {
  if (line.startsWith('+++') || line.startsWith('---')) {
    return <div className="text-slate-400 font-semibold">{line}</div>
  }
  if (line.startsWith('+')) {
    return <div className="bg-emerald-950/60 text-emerald-300 border-l-2 border-emerald-500 pl-1">{line}</div>
  }
  if (line.startsWith('-')) {
    return <div className="bg-red-950/60 text-red-300 border-l-2 border-red-500 pl-1">{line}</div>
  }
  if (line.startsWith('@@')) {
    return <div className="text-blue-400 mt-2">{line}</div>
  }
  if (line.startsWith('diff') || line.startsWith('index')) {
    return <div className="text-slate-500 mt-3 pb-1 border-b border-slate-800">{line}</div>
  }
  return <div className="text-slate-400">{line}</div>
}

export default function DiffViewer({ runId }) {
  const [diff, setDiff] = useState(null)

  useEffect(() => {
    fetchDiff(runId).then(d => setDiff(d.diff)).catch(() => setDiff(''))
  }, [runId])

  if (diff === null) {
    return <div className="p-4 text-slate-500 text-xs animate-pulse">Loading diff…</div>
  }

  if (!diff) {
    return (
      <div className="p-6 flex flex-col items-center justify-center h-full gap-2 text-slate-600">
        <div className="text-3xl opacity-20">Δ</div>
        <p className="text-xs">No diff available yet — run the pipeline first</p>
      </div>
    )
  }

  const lines = diff.split('\n')

  return (
    <div
      className="h-full overflow-auto p-4"
      style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: '0.72rem', lineHeight: '1.65' }}
    >
      {lines.map((line, i) => (
        <DiffLine key={i} line={line} />
      ))}
    </div>
  )
}
