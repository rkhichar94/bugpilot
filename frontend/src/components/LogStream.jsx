import { useState, useEffect, useRef } from 'react'
import { fetchLogs } from '../api'

function colorize(line) {
  if (line.includes('FAILED') || line.includes('ERROR') || line.includes('error'))
    return 'text-red-400'
  if (line.includes('PASSED') || line.includes('SUCCESS') || line.includes('created'))
    return 'text-emerald-400'
  if (line.includes('[fix_generator]') || line.includes('Tool call'))
    return 'text-blue-300'
  if (line.includes('[issue_analyst]'))
    return 'text-purple-300'
  if (line.includes('[pr_creator]'))
    return 'text-amber-300'
  if (line.includes('[test_runner]'))
    return 'text-teal-300'
  return 'text-slate-300'
}

export default function LogStream({ runId, done }) {
  const [lines, setLines] = useState([])
  const [offset, setOffset] = useState(0)
  const bottomRef = useRef(null)
  const stoppedRef = useRef(false)

  useEffect(() => {
    setLines([])
    setOffset(0)
    stoppedRef.current = false
  }, [runId])

  useEffect(() => {
    if (stoppedRef.current) return
    let localOffset = offset

    const poll = async () => {
      if (stoppedRef.current) return
      try {
        const data = await fetchLogs(runId, localOffset)
        if (data.lines.length > 0) {
          setLines(prev => [...prev, ...data.lines])
          localOffset = data.offset
          setOffset(data.offset)
        }
        if (data.done) {
          stoppedRef.current = true
        }
      } catch (_) {}
    }

    poll()
    if (!done) {
      const t = setInterval(poll, 1000)
      return () => clearInterval(t)
    }
  }, [runId, done])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lines])

  return (
    <div
      className="h-full overflow-y-auto p-4 space-y-0.5"
      style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: '0.72rem', lineHeight: '1.6' }}
    >
      {lines.length === 0 && (
        <span className="text-slate-600 animate-pulse">Waiting for pipeline output…</span>
      )}
      {lines.map((line, i) => (
        <div key={i} className={`log-line px-1 rounded ${colorize(line)}`}>
          {line || ' '}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
