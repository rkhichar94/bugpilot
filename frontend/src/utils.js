export function formatDistanceToNow(unixTs) {
  if (!unixTs) return ''
  const secs = Math.floor(Date.now() / 1000 - unixTs)
  if (secs < 60) return 'just now'
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`
  return `${Math.floor(secs / 86400)}d ago`
}
