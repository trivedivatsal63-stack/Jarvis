import { useEffect, useRef, useCallback } from 'react'

const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const WS_URL = `${WS_PROTOCOL}//${window.location.host}/ws`

export default function useWebSocket(onMessage) {
  const ws = useRef(null)
  const reconnectTimer = useRef(null)

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return
    ws.current = new WebSocket(WS_URL)

    ws.current.onopen = () => {
      console.log('[WS] Connected')
    }

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch (e) {
        console.error('[WS] Parse error:', e)
      }
    }

    ws.current.onclose = () => {
      console.log('[WS] Disconnected, reconnecting in 3s...')
      reconnectTimer.current = setTimeout(connect, 3000)
    }

    ws.current.onerror = () => {
      ws.current?.close()
    }
  }, [onMessage])

  const send = useCallback((data) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data))
      return true
    }
    return false
  }, [])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      ws.current?.close()
    }
  }, [connect])

  return { send, isConnected: () => ws.current?.readyState === WebSocket.OPEN }
}
