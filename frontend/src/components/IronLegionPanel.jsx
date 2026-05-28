import React, { useState } from 'react'

const BRIEFING_TASKS = [
  { description: 'Analyze weather and news', status: 'pending' },
  { description: 'Check system vitals', status: 'pending' },
  { description: 'Review schedule and alerts', status: 'pending' },
  { description: 'Prepare daily summary', status: 'pending' },
]

export default function IronLegionPanel({ onDeploy, onBriefing, subtasks = [], synthesis = '', isProcessing = false }) {
  const [input, setInput] = useState('')

  const handleDeploy = () => {
    if (!input.trim() || isProcessing) return
    if (onDeploy) onDeploy(input.trim())
    setInput('')
  }

  const handleBriefing = () => {
    if (onBriefing) {
      onBriefing(BRIEFING_TASKS)
    }
  }

  const statusClass = (status) => {
    switch (status) {
      case 'running': return 'legion-status-running'
      case 'done': return 'legion-status-done'
      default: return 'legion-status-pending'
    }
  }

  return (
    <div className="legion-panel">
      <div className="panel-header">
        <span className="panel-dot" />
        IRON LEGION
        {isProcessing && <span className="legion-processing">PROCESSING</span>}
      </div>

      <div className="legion-input-area">
        <textarea
          className="legion-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleDeploy() }}}
          placeholder="Deploy task, Sir..."
          disabled={isProcessing}
          rows={2}
        />
        <button className="legion-deploy-btn" onClick={handleDeploy} disabled={!input.trim() || isProcessing}>
          DEPLOY
        </button>
      </div>

      <div className="legion-shortcuts">
        <button className="legion-briefing-btn" onClick={handleBriefing} disabled={isProcessing}>
          MORNING BRIEFING
        </button>
      </div>

      {(subtasks.length > 0 || isProcessing) && (
        <div className="legion-subtasks">
          <div className="legion-subtasks-title">SUBTASKS</div>
          {(isProcessing && subtasks.length === 0 ? BRIEFING_TASKS : subtasks).map((t, i) => (
            <div key={i} className="legion-subtask">
              <span className="legion-subtask-desc">{t.description}</span>
              <span className={`legion-status ${statusClass(t.status)}`}>
                {t.status.toUpperCase()}
              </span>
            </div>
          ))}
        </div>
      )}

      {synthesis && (
        <div className="legion-synthesis">
          <div className="legion-synthesis-title">SYNTHESIS</div>
          <div className="legion-synthesis-content">{synthesis}</div>
        </div>
      )}
    </div>
  )
}
