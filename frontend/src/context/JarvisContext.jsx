import React, { createContext, useContext, useReducer, useCallback } from 'react'

const JarvisContext = createContext(null)

const initialState = {
  activeTab: 'chat',
  stats: null,
  reminders: [],
  activeReminder: null,
  messages: [],
  streaming: false,
  thinking: false,
  connected: false,
  cameraOn: false,
  audioOn: true,
  isMuted: false,
  volume: 80,
  faces: [],
  objects: [],
  threat: false,
  devices: [],
  brightness: 80,
  subtasks: [],
  synthesis: '',
  legionProcessing: false,
  notes: [],
  noteSearch: '',
}

function reducer(state, action) {
  switch (action.type) {
    case 'SET_TAB':
      return { ...state, activeTab: action.payload }
    case 'SET_STATS':
      return { ...state, stats: action.payload }
    case 'ADD_REMINDER':
      return { ...state, reminders: [...state.reminders, action.payload], activeReminder: action.payload }
    case 'DISMISS_REMINDER':
      return { ...state, activeReminder: null }
    case 'SET_CONNECTED':
      return { ...state, connected: action.payload }
    case 'SET_CAMERA':
      return { ...state, cameraOn: action.payload }
    case 'SET_AUDIO':
      return { ...state, audioOn: action.payload }
    case 'SET_MUTED':
      return { ...state, isMuted: action.payload }
    case 'SET_VOLUME':
      return { ...state, volume: action.payload }
    case 'SET_STREAMING':
      return { ...state, streaming: action.payload, thinking: action.payload }
    case 'SET_THINKING':
      return { ...state, thinking: action.payload }
    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] }
    case 'UPDATE_LAST_MESSAGE':
      const msgs = [...state.messages]
      if (msgs.length > 0) msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], text: action.payload }
      return { ...state, messages: msgs }
    case 'SET_FACES':
      return { ...state, faces: action.payload }
    case 'SET_OBJECTS':
      return { ...state, objects: action.payload }
    case 'SET_THREAT':
      return { ...state, threat: action.payload }
    case 'SET_DEVICES':
      return { ...state, devices: action.payload }
    case 'SET_BRIGHTNESS':
      return { ...state, brightness: action.payload }
    case 'SET_SUBTASKS':
      return { ...state, subtasks: action.payload }
    case 'SET_SYNTHESIS':
      return { ...state, synthesis: action.payload }
    case 'SET_LEGION_PROCESSING':
      return { ...state, legionProcessing: action.payload }
    case 'SET_NOTES':
      return { ...state, notes: action.payload }
    case 'SET_NOTE_SEARCH':
      return { ...state, noteSearch: action.payload }
    default:
      return state
  }
}

export function JarvisProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)

  return (
    <JarvisContext.Provider value={{ state, dispatch }}>
      {children}
    </JarvisContext.Provider>
  )
}

export function useJarvis() {
  const ctx = useContext(JarvisContext)
  if (!ctx) throw new Error('useJarvis must be used within JarvisProvider')
  return ctx
}
