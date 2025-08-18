import React from 'react'

type Props = {
  modalities: string[]
  onToggle: (m: string) => void
  onScreenshot: () => void
  useIcons?: boolean
}

const all = ['text','clipboard','screenshot','audio','system-audio']

const modalityIcons: Record<string, string> = {
  text: '📝',
  clipboard: '📋', 
  screenshot: '💻',
  audio: '🎤',
  'system-audio': '🔊'
}

const ModalityBar: React.FC<Props> = ({ modalities, onToggle, onScreenshot, useIcons = false }) => {
  return (
    <div className="mods">
      {all.map((m, i) => (
        <button
          key={m}
          className={modalities.includes(m) ? 'active' : ''}
          onClick={() => m === 'screenshot' ? onScreenshot() : onToggle(m)}
          title={useIcons ? `${m} (Ctrl+${i+1})` : `Ctrl+${i+1}`}
        >
          {useIcons ? modalityIcons[m] || m : m}
        </button>
      ))}
    </div>
  )
}

export default ModalityBar
