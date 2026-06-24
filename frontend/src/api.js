const BASE = '/api'

export async function fetchRuns() {
  const r = await fetch(`${BASE}/runs`)
  if (!r.ok) throw new Error('Failed to fetch runs')
  return r.json()
}

export async function fetchRun(id) {
  const r = await fetch(`${BASE}/runs/${id}`)
  if (!r.ok) throw new Error('Run not found')
  return r.json()
}

export async function fetchLogs(id, offset = 0) {
  const r = await fetch(`${BASE}/runs/${id}/logs?offset=${offset}`)
  if (!r.ok) throw new Error('Failed to fetch logs')
  return r.json()
}

export async function fetchDiff(id) {
  const r = await fetch(`${BASE}/runs/${id}/diff`)
  if (!r.ok) return { diff: '' }
  return r.json()
}

export async function startRun(issueKey, summary = '') {
  const r = await fetch(`${BASE}/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ issue_key: issueKey, summary }),
  })
  if (!r.ok) throw new Error('Failed to start run')
  return r.json()
}

export async function approveRun(id) {
  const r = await fetch(`${BASE}/runs/${id}/approve`, { method: 'POST' })
  return r.json()
}

export async function rejectRun(id) {
  const r = await fetch(`${BASE}/runs/${id}/reject`, { method: 'POST' })
  return r.json()
}
