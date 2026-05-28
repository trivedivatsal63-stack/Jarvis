import React from 'react'

export default function RemindersPanel({ activeReminder, onDismiss, upcomingReminders }) {
  if (!activeReminder) return null

  const upcoming = upcomingReminders?.filter(r => r !== activeReminder) ?? []

  return (
    <div className="reminders-overlay" onClick={onDismiss}>
      <div className="reminders-panel" onClick={(e) => e.stopPropagation()}>
        <div className="reminders-header">
          <span className="reminders-header-icon">{'\u26A0\uFE0F'}</span>
          <span className="reminders-header-text">REMINDER</span>
        </div>

        <div className="reminders-body">
          <div className="reminders-message">
            {activeReminder.message || activeReminder.text || String(activeReminder)}
          </div>

          <button className="reminders-dismiss-btn" onClick={onDismiss}>
            DISMISS
          </button>

          {upcoming.length > 0 && (
            <div className="reminders-upcoming">
              <div className="reminders-upcoming-label">UPCOMING</div>
              <div className="reminders-upcoming-list">
                {upcoming.map((r, i) => (
                  <div key={i} className="reminders-upcoming-item">
                    {r.message || r.text || String(r)}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
