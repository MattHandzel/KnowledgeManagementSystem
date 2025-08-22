import React, { useState, useRef, useEffect } from 'react'
import { isNative } from '../shared/platform'

type Props = {
  onAudioReady: (file: File) => void
  systemAudio?: boolean
}

const AudioRecorder: React.FC<Props> = ({ onAudioReady, systemAudio = false }) => {
  const [isRecording, setIsRecording] = useState(false)
  const [audioData, setAudioData] = useState<number[]>([])
  const [error, setError] = useState<string>('')
  const websocketRef = useRef<WebSocket | null>(null)
  const recorderId = useRef<string>('')
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const mediaChunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)


  useEffect(() => {
    return () => {
      if (websocketRef.current) {
        websocketRef.current.close()
      }
    }
  }, [])

  const startRecording = async () => {
    try {
      setError('')
      setAudioData([])

      if (isNative()) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        streamRef.current = stream
        const mr = new MediaRecorder(stream)
        mediaRecorderRef.current = mr
        mediaChunksRef.current = []
        mr.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) {
            mediaChunksRef.current.push(e.data)
          }
        }
        mr.start()
        setIsRecording(true)
        return
      }

      const recorderType = systemAudio ? 'system' : 'microphone'
      recorderId.current = `${recorderType}_${Date.now()}`
      
      const formData = new FormData()
      formData.append('recorder_type', recorderType)
      formData.append('recorder_id', recorderId.current)
      
      const response = await fetch('/api/audio/start', {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to start recording')
      }
      
      setIsRecording(true)
      
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${wsProtocol}//${window.location.host}/ws/audio-waveform/${recorderId.current}`
      websocketRef.current = new WebSocket(wsUrl)
      
      websocketRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'waveform' && data.recorder_id === recorderId.current) {
            setAudioData(prev => [...prev.slice(-100), ...data.data].slice(-100))
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }
      
      websocketRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setError('WebSocket connection failed')
      }
      
    } catch (error) {
      console.error('Recording failed:', error)
      setError(error instanceof Error ? error.message : 'Recording failed')
      setIsRecording(false)
    }
  }

  const stopRecording = async () => {
    try {
      if (isNative()) {
        const mr = mediaRecorderRef.current
        if (!mr) {
          throw new Error('No active recording')
        }
        const done: Promise<File> = new Promise((resolve, reject) => {
          mr.onstop = () => {
            try {
              const blob = new Blob(mediaChunksRef.current, { type: mr.mimeType || 'audio/webm' })
              const ext = blob.type.includes('mp4') || blob.type.includes('m4a') ? 'm4a' : (blob.type.includes('webm') ? 'webm' : 'wav')
              const name = `audio_${Date.now()}.${ext}`
              const file = new File([blob], name, { type: blob.type || 'audio/webm' })
              resolve(file)
            } catch (e) {
              reject(e)
            }
          }
        })
        mr.stop()
        const file = await done
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(t => t.stop())
          streamRef.current = null
        }
        mediaRecorderRef.current = null
        mediaChunksRef.current = []
        setIsRecording(false)
        onAudioReady(file)
        return
      }

      if (websocketRef.current) {
        websocketRef.current.close()
        websocketRef.current = null
      }
      
      const formData = new FormData()
      formData.append('recorder_id', recorderId.current)
      
      const response = await fetch('/api/audio/stop', {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to stop recording')
      }
      
      const result = await response.json()
      
      const audioResponse = await fetch(`/capture/raw_capture/media/${result.filename}`)
      if (!audioResponse.ok) {
        throw new Error('Failed to fetch recorded audio file')
      }
      
      const audioBlob = await audioResponse.blob()
      const audioFile = new File([audioBlob], result.filename, { type: 'audio/wav' })
      
      setIsRecording(false)
      onAudioReady(audioFile)
      
    } catch (error) {
      console.error('Stop recording failed:', error)
      setError(error instanceof Error ? error.message : 'Failed to stop recording')
      setIsRecording(false)
    }
  }

  return (
    <div className="audio-recorder" style={{ padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}>
      {error && (
        <div style={{ 
          color: '#dc3545', 
          fontSize: '12px', 
          marginBottom: '10px',
          padding: '5px',
          backgroundColor: '#f8d7da',
          borderRadius: '2px'
        }}>
          {error}
        </div>
      )}
      <div className="waveform" style={{ 
        display: 'flex', 
        alignItems: 'end', 
        height: '60px', 
        gap: '1px',
        backgroundColor: '#f5f5f5',
        padding: '5px',
        borderRadius: '2px',
        marginBottom: '10px'
      }}>
        {audioData.length === 0 && !isRecording && (
          <div style={{ color: '#666', fontSize: '12px', alignSelf: 'center' }}>
            Waveform will appear here during recording
          </div>
        )}
        {audioData.map((value, i) => (
          <div 
            key={i} 
            className="bar" 
            style={{ 
              height: `${Math.max(2, Math.min(50, value))}px`, 
              width: '2px', 
              backgroundColor: isRecording ? '#007acc' : '#999',
              borderRadius: '1px'
            }} 
          />
        ))}
      </div>
      <div>
        {!isRecording ? (
          <button 
            onClick={startRecording}
            style={{
              padding: '8px 16px',
              backgroundColor: '#007acc',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            🎤 Record {systemAudio ? 'System Audio' : 'Microphone'}
          </button>
        ) : (
          <button 
            onClick={stopRecording}
            style={{
              padding: '8px 16px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            ⏹️ Stop Recording
          </button>
        )}
      </div>
    </div>
  )
}

export default AudioRecorder
