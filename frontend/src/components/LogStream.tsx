import { useRef, useEffect } from 'react'

interface LogEntry {
  agent: string
  type: string
  data: Record<string, unknown>
}

interface Props {
  logs: LogEntry[]
}

export function LogStream({ logs }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  return (
    <div className="log-stream">
      {logs.length === 0 && (
        <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>
          等待 Agent 运行日志... / Waiting for agent logs...
        </div>
      )}
      {logs.map((log, i) => (
        <div key={i} className="log-entry">
          <span className="agent-name">[{log.agent}]</span>{' '}
          <span className="log-type">{log.type}</span>{' '}
          <span>{JSON.stringify(log.data)}</span>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
