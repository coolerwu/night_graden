import React from 'react'

const AGENTS = [
  { key: 'market_sensor', label: '市场感知' },
  { key: 'strategy_engine', label: '策略引擎' },
  { key: 'risk_guardian', label: '风控守卫' },
  { key: 'trade_executor', label: '交易执行' },
  { key: 'asset_manager', label: '资产管家' },
]

interface Props {
  currentAgent: string
  completedAgents: string[]
}

export function AgentPipeline({ currentAgent, completedAgents }: Props) {
  return (
    <div className="pipeline">
      {AGENTS.map((agent, i) => (
        <React.Fragment key={agent.key}>
          {i > 0 && <span className="pipeline-arrow">&rarr;</span>}
          <span
            className={`pipeline-node ${
              currentAgent === agent.key
                ? 'active'
                : completedAgents.includes(agent.key)
                ? 'done'
                : ''
            }`}
          >
            {agent.label}
          </span>
        </React.Fragment>
      ))}
    </div>
  )
}
