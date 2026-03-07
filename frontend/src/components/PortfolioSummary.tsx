interface Portfolio {
  total_value: number
  cash_balance: number
  max_drawdown_pct: number
  total_realized_pnl: number
  positions: Array<{
    symbol: string
    quantity: number
    current_price: number
  }>
}

interface Props {
  portfolio: Portfolio | null
}

export function PortfolioSummary({ portfolio }: Props) {
  if (!portfolio) {
    return (
      <div className="card">
        <h2>资产概览 / Portfolio</h2>
        <div style={{ color: 'var(--text-secondary)' }}>暂无数据</div>
      </div>
    )
  }

  const pnl = portfolio.total_realized_pnl || 0

  return (
    <div className="card">
      <h2>资产概览 / Portfolio</h2>
      <div className="stat-grid">
        <div className="stat-item">
          <div className="label">总资产</div>
          <div className="value">${portfolio.total_value.toFixed(2)}</div>
        </div>
        <div className="stat-item">
          <div className="label">可用余额</div>
          <div className="value">${portfolio.cash_balance.toFixed(2)}</div>
        </div>
        <div className="stat-item">
          <div className="label">盈亏 PnL</div>
          <div className={`value ${pnl >= 0 ? 'positive' : 'negative'}`}>
            {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}
          </div>
        </div>
        <div className="stat-item">
          <div className="label">最大回撤</div>
          <div className={`value ${portfolio.max_drawdown_pct > 5 ? 'negative' : ''}`}>
            {portfolio.max_drawdown_pct.toFixed(2)}%
          </div>
        </div>
      </div>
    </div>
  )
}
