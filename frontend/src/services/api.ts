const API_BASE = '/api'

export interface TradingStatus {
  running: boolean
  has_result: boolean
  error: string | null
}

export interface TradingResult {
  status: string
  portfolio?: {
    total_value: number
    cash_balance: number
    max_drawdown_pct: number
    total_realized_pnl: number
    peak_value: number
    positions: Array<{
      symbol: string
      quantity: number
      current_price: number
    }>
  }
  messages?: Array<{
    agent: string
    type: string
    data: Record<string, unknown>
  }>
  iteration?: number
  error?: string
}

export async function startTrading(params: {
  symbol?: string
  mode?: string
  initial_capital?: number
}) {
  const res = await fetch(`${API_BASE}/trading/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  return res.json()
}

export async function getTradingStatus(): Promise<TradingStatus> {
  const res = await fetch(`${API_BASE}/trading/status`)
  return res.json()
}

export async function getTradingResult(): Promise<TradingResult> {
  const res = await fetch(`${API_BASE}/trading/result`)
  return res.json()
}

export async function stopTrading() {
  const res = await fetch(`${API_BASE}/trading/stop`, { method: 'POST' })
  return res.json()
}

export async function getPortfolioSnapshot() {
  const res = await fetch(`${API_BASE}/portfolio/snapshot`)
  return res.json()
}

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`)
  return res.json()
}
