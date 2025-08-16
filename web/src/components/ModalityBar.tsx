import React from 'react'

type Props = {
  modalities: string[]
  onToggle: (m: string) => void
  onScreenshot: () => void
}

const all = ['text','clipboard','screenshot','audio','files']

const ModalityBar: React.FC<Props> = ({ modalities, onToggle, onScreenshot }) => {
  return (
    <div className="mods">
      {all.map((m, i) => (
        <button
          key={m}
          className={modalities.includes(m) ? 'active' : ''}
          onClick={() => m === 'screenshot' ? onScreenshot() : onToggle(m)}
          title={`Ctrl+${i+1}`}
        >
          {m}
        </button>
      ))}
    </div>
  )
}

export default ModalityBar
