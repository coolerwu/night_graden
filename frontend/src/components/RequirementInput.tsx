import { useState } from 'react'

interface Props {
  onSubmit: (requirement: string, config: { symbol: string; mode: string; capital: number }) => void
  disabled: boolean
}

const PRESETS = [
  '对 BTC/USDT 执行均线交叉策略，初始资金 10000 USDT',
  '用网格交易策略交易 ETH/USDT，网格间距 2%',
  '分析当前 BTC 市场趋势并自动执行交易',
]

export function RequirementInput({ onSubmit, disabled }: Props) {
  const [text, setText] = useState('')
  const [symbol, setSymbol] = useState('BTC/USDT')
  const [mode, setMode] = useState('mock')
  const [capital, setCapital] = useState(10000)

  const handleSubmit = () => {
    if (!text.trim()) return
    onSubmit(text.trim(), { symbol, mode, capital })
  }

  return (
    <div className="card">
      <h2>提交需求 / Submit Requirement</h2>
      <div className="requirement-form">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="描述你的交易需求... / Describe your trading requirement..."
          disabled={disabled}
        />

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>交易对</label>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              disabled={disabled}
              style={{
                display: 'block',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)',
                padding: '6px 10px',
                borderRadius: '4px',
                marginTop: '4px',
              }}
            >
              <option value="BTC/USDT">BTC/USDT</option>
              <option value="ETH/USDT">ETH/USDT</option>
              <option value="SOL/USDT">SOL/USDT</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>模式</label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              disabled={disabled}
              style={{
                display: 'block',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)',
                padding: '6px 10px',
                borderRadius: '4px',
                marginTop: '4px',
              }}
            >
              <option value="mock">模拟 Mock</option>
              <option value="live">实盘 Live</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>初始资金</label>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(Number(e.target.value))}
              disabled={disabled}
              style={{
                display: 'block',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)',
                padding: '6px 10px',
                borderRadius: '4px',
                width: '120px',
                marginTop: '4px',
              }}
            />
          </div>
        </div>

        <div className="btn-group">
          <button className="btn btn-primary" onClick={handleSubmit} disabled={disabled || !text.trim()}>
            {disabled ? '运行中...' : '启动交易 / Start Trading'}
          </button>
        </div>

        <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
          快捷模板 / Quick Templates:
          {PRESETS.map((preset, i) => (
            <div
              key={i}
              onClick={() => !disabled && setText(preset)}
              style={{
                cursor: disabled ? 'default' : 'pointer',
                padding: '4px 0',
                opacity: disabled ? 0.5 : 1,
              }}
            >
              &bull; {preset}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
