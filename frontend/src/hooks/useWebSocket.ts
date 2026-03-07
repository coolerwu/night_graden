import { useEffect, useRef, useState, useCallback } from 'react'

export interface WSMessage {
  agent: string
  type: string
  data: Record<string, unknown>
}

export function useWebSocket(url: string) {
  const [messages, setMessages] = useState<WSMessage[]>([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        setMessages((prev) => [...prev, msg])
      } catch {
        // ignore non-JSON messages
      }
    }

    return () => {
      ws.close()
    }
  }, [url])

  const clearMessages = useCallback(() => setMessages([]), [])

  return { messages, connected, clearMessages }
}
