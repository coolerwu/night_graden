import { useState, useEffect, useCallback } from 'react'
import { RequirementInput } from './components/RequirementInput'
import { AgentPipeline } from './components/AgentPipeline'
import { LogStream } from './components/LogStream'
import { PortfolioSummary } from './components/PortfolioSummary'
import { startTrading, getTradingStatus, getTradingResult, stopTrading, type TradingResult } from './services/api'

type SessionStatus = 'idle' | 'running' | 'completed' | 'error'

function App() {
  const [status, setStatus] = useState<SessionStatus>('idle')
  const [result, setResult] = useState<TradingResult | null>(null)
  const [logs, setLogs] = useState<Array<{ agent: string; type: string; data: Record<string, unknown> }>>([])
  const [currentAgent, setCurrentAgent] = useState('')
  const [completedAgents, setCompletedAgents] = useState<string[]>([])

  // Poll for status when running
  useEffect(() => {
    if (status !== 'running') return
    const interval = setInterval(async () => {
      try {
        const s = await getTradingStatus()
        if (!s.running) {
          const r = await getTradingResult()
          setResult(r)
          setStatus(r.error ? 'error' : 'completed')
          if (r.messages) {
            setLogs(r.messages)
            // Determine completed agents from messages
            const agents = r.messages.map((m) => m.agent)
            setCompletedAgents([...new Set(agents)])
            setCurrentAgent('')
          }
        }
      } catch {
        // ignore polling errors
      }
    }, 1000)
    return () => clearInterval(interval)
  }, [status])

  const handleSubmit = useCallback(
    async (_requirement: string, config: { symbol: string; mode: string; capital: number }) => {
      setStatus('running')
      setResult(null)
      setLogs([])
      setCompletedAgents([])
      setCurrentAgent('market_sensor')

      try {
        await startTrading({
          symbol: config.symbol,
          mode: config.mode,
          initial_capital: config.capital,
        })
      } catch {
        setStatus('error')
      }
    },
    [],
  )

  const handleStop = useCallback(async () => {
    await stopTrading()
    setStatus('idle')
    setCurrentAgent('')
  }, [])

  return (
    <div className="app">
      <header className="header">
        <h1>Night Garden / 夜花园</h1>
        <div className="subtitle">
          Multi-Agent Quantitative Trading System / 多智能体量化交易系统
        </div>
      </header>

      <div style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span className={`status-badge ${status}`}>
          {status === 'idle' && '空闲 Idle'}
          {status === 'running' && '运行中 Running...'}
          {status === 'completed' && '完成 Completed'}
          {status === 'error' && '错误 Error'}
        </span>
        {status === 'running' && (
          <button className="btn btn-danger" onClick={handleStop} style={{ padding: '4px 12px', fontSize: '12px' }}>
            停止 / Stop
          </button>
        )}
      </div>

      <AgentPipeline currentAgent={currentAgent} completedAgents={completedAgents} />

      <div className="grid-2">
        <div>
          <RequirementInput onSubmit={handleSubmit} disabled={status === 'running'} />
        </div>
        <div>
          <PortfolioSummary portfolio={result?.portfolio || null} />
        </div>
      </div>

      <div className="card">
        <h2>Agent 运行日志 / Agent Logs</h2>
        <LogStream logs={logs} />
      </div>

      {result?.error && (
        <div className="card" style={{ borderColor: 'var(--accent-red)' }}>
          <h2 style={{ color: 'var(--accent-red)' }}>Error</h2>
          <pre style={{ color: 'var(--accent-red)' }}>{result.error}</pre>
        </div>
      )}
    </div>
  )
}

export default App
