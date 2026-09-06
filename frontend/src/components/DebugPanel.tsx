type DebugProps = { debug?: string }

export default function DebugPanel({ debug }: DebugProps) {
  if (!debug) return null
  return <div className="debug-panel">{debug}</div>
}