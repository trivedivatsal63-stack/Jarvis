import React, { useState, useCallback, useEffect } from 'react'
import { JarvisProvider, useJarvis } from './context/JarvisContext'
import HudOverlay from './components/HudOverlay'
import BootSequence from './components/BootSequence'
import TopNav from './components/TopNav'
import SystemStats from './components/SystemStats'
import WeatherWidget from './components/WeatherWidget'
import NewsWidget from './components/NewsWidget'
import ChatPanel from './components/ChatPanel'
import VisionPanel from './components/VisionPanel'
import SmartHomePanel from './components/SmartHomePanel'
import IronLegionPanel from './components/IronLegionPanel'
import NotesPanel from './components/NotesPanel'
import RemindersPanel from './components/RemindersPanel'
import VoiceOutput from './components/VoiceOutput'
import useWebSocket from './hooks/useWebSocket'

const API = '/api'

function AppContent() {
  const { state, dispatch } = useJarvis()
  const [booted, setBooted] = useState(false)

  const handleWsMessage = useCallback((data) => {
    if (data.type === 'stats') dispatch({ type: 'SET_STATS', payload: data.data })
    if (data.type === 'reminder') dispatch({ type: 'ADD_REMINDER', payload: data.data })
  }, [dispatch])

  const { send: wsSend, isConnected } = useWebSocket(handleWsMessage)

  useEffect(() => {
    dispatch({ type: 'SET_CONNECTED', payload: isConnected?.() ?? false })
  }, [isConnected, dispatch])

  const handleTabChange = (tab) => dispatch({ type: 'SET_TAB', payload: tab })

  const handleScan = async () => {
    try {
      const res = await fetch(`${API}/vision/scan`, { method: 'POST' })
      const data = await res.json()
      if (data.objects) dispatch({ type: 'SET_OBJECTS', payload: data.objects })
      if (data.threat) dispatch({ type: 'SET_THREAT', payload: data.threat })
    } catch {}
  }

  const handleRegister = async (name, blob) => {
    try {
      const form = new FormData()
      form.append('file', blob)
      await fetch(`${API}/vision/register?name=${encodeURIComponent(name)}`, { method: 'POST', body: form })
    } catch {}
  }

  const handleDeviceControl = async (entityId, action) => {
    try {
      await fetch(`${API}/home/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entity_id: entityId, action }),
      })
    } catch {}
  }

  const handleBrightnessChange = (val) => dispatch({ type: 'SET_BRIGHTNESS', payload: val })

  const handleDeploy = async (task) => {
    dispatch({ type: 'SET_LEGION_PROCESSING', payload: true })
    try {
      const res = await fetch(`${API}/legion/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task }),
      })
      const data = await res.json()
      if (data.subtasks) dispatch({ type: 'SET_SUBTASKS', payload: data.subtasks })
      if (data.synthesis) dispatch({ type: 'SET_SYNTHESIS', payload: data.synthesis })
    } catch {}
    dispatch({ type: 'SET_LEGION_PROCESSING', payload: false })
  }

  const handleBriefing = async () => {
    dispatch({ type: 'SET_LEGION_PROCESSING', payload: true })
    try {
      const res = await fetch(`${API}/legion/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: 'Morning briefing: weather, news, system status' }),
      })
      const data = await res.json()
      if (data.subtasks) dispatch({ type: 'SET_SUBTASKS', payload: data.subtasks })
      if (data.synthesis) dispatch({ type: 'SET_SYNTHESIS', payload: data.synthesis })
    } catch {}
    dispatch({ type: 'SET_LEGION_PROCESSING', payload: false })
  }

  const handleDismissReminder = () => dispatch({ type: 'DISMISS_REMINDER' })

  const handleVolumeChange = (v) => dispatch({ type: 'SET_VOLUME', payload: v })
  const handleMuteToggle = () => dispatch({ type: 'SET_MUTED', payload: !state.isMuted })

  const handleCameraToggle = () => dispatch({ type: 'SET_CAMERA', payload: !state.cameraOn })
  const handleAudioToggle = () => dispatch({ type: 'SET_AUDIO', payload: !state.audioOn })

  if (!booted) {
    return <BootSequence onComplete={() => setBooted(true)} />
  }

  const showLeftPanel = state.activeTab === 'chat'
  const showRightPanel = state.activeTab === 'chat'

  return (
    <>
      <HudOverlay />
      <TopNav
        activeTab={state.activeTab}
        onTabChange={handleTabChange}
        connected={state.connected}
        cameraOn={state.cameraOn}
        audioOn={state.audioOn}
        onCameraToggle={handleCameraToggle}
        onAudioToggle={handleAudioToggle}
      />

      <RemindersPanel
        activeReminder={state.activeReminder}
        onDismiss={handleDismissReminder}
        upcomingReminders={state.reminders}
      />

      <div className="jarvis-app" style={{ paddingTop: 40 }}>
        {showLeftPanel && (
          <div className="panel panel-left">
            <SystemStats stats={state.stats} />
            <VoiceOutput
              isSpeaking={false}
              volume={state.volume}
              onVolumeChange={handleVolumeChange}
              onMuteToggle={handleMuteToggle}
              isMuted={state.isMuted}
            />
          </div>
        )}

        <div className={`panel panel-center ${!showLeftPanel ? 'panel-full' : ''}`}>
          {state.activeTab === 'chat' && <ChatPanel wsSend={wsSend} />}
          {state.activeTab === 'vision' && <VisionPanel onScan={handleScan} onRegister={handleRegister} threats={state.threat} faces={state.faces} objects={state.objects} />}
          {state.activeTab === 'home' && (
            <SmartHomePanel
              devices={state.devices}
              onControl={handleDeviceControl}
              brightness={state.brightness}
              onBrightnessChange={handleBrightnessChange}
            />
          )}
          {state.activeTab === 'legion' && (
            <IronLegionPanel
              onDeploy={handleDeploy}
              onBriefing={handleBriefing}
              subtasks={state.subtasks}
              synthesis={state.synthesis}
              isProcessing={state.legionProcessing}
            />
          )}
          {state.activeTab === 'notes' && <NotesPanel />}
          {state.activeTab === 'files' && (
            <div className="placeholder-panel">
              <div className="placeholder-icon">\uD83D\uDCC1</div>
              <div className="placeholder-text">FILE SYSTEM</div>
              <div className="placeholder-sub">Coming online, Sir.</div>
            </div>
          )}
        </div>

        {showRightPanel && (
          <div className="panel panel-right">
            <WeatherWidget />
            <NewsWidget />
            <div className="hud-footer">
              <div className="hud-footer-line">J.A.R.V.I.S v4.1</div>
              <div className="hud-footer-line">SYSTEM: {state.stats ? 'ONLINE' : 'CONNECTING...'}</div>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

export default function App() {
  return (
    <JarvisProvider>
      <AppContent />
    </JarvisProvider>
  )
}
