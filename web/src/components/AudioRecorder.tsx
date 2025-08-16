import React, { useState, useRef, useEffect } from 'react'

type Props = {
  onAudioReady: (file: File) => void
  systemAudio?: boolean
}

const AudioRecorder: React.FC<Props> = ({ onAudioReady, systemAudio = false }) => {
  const [isRecording, setIsRecording] = useState(false)
  const [audioData, setAudioData] = useState<number[]>([])
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const startRecording = async () => {
    try {
      const constraints = systemAudio 
        ? { audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false } }
        : { audio: true }
      
      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      streamRef.current = stream
      
      audioContextRef.current = new AudioContext()
      analyserRef.current = audioContextRef.current.createAnalyser()
      analyserRef.current.fftSize = 256
      
      const source = audioContextRef.current.createMediaStreamSource(stream)
      source.connect(analyserRef.current)
      
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      const chunks: Blob[] = []
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data)
        }
      }
      
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' })
        const audioFile = new File([audioBlob], `${systemAudio ? 'system_' : ''}audio_${Date.now()}.webm`, { type: 'audio/webm' })
        onAudioReady(audioFile)
      }
      
      mediaRecorderRef.current.start(100)
      setIsRecording(true)
      setAudioData([])
      
      visualizeAudio()
    } catch (error) {
      console.error('Recording failed:', error)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
      
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }

  const visualizeAudio = () => {
    if (!analyserRef.current) return
    
    const bufferLength = analyserRef.current.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)
    
    const draw = () => {
      if (!isRecording) return
      
      analyserRef.current!.getByteTimeDomainData(dataArray)
      const average = dataArray.reduce((sum, value) => sum + Math.abs(value - 128), 0) / bufferLength
      setAudioData(prev => [...prev.slice(-100), average])
      
      requestAnimationFrame(draw)
    }
    draw()
  }

  return (
    <div className="audio-recorder" style={{ padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}>
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
              height: `${Math.max(2, Math.min(50, value * 2))}px`, 
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
