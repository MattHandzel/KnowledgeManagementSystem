import React from 'react'

const HelpOverlay: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  return (
    <div className="help">
      <div className="panel">
        <div className="hdr">
          <span>Help</span>
          <button onClick={onClose}>Close</button>
        </div>
        <pre>
Ctrl+S save
Ctrl+1..9 toggle modalities
Tab/Shift+Tab navigate inputs
ESC normal mode / clear
C context mode (from normal)
F1 toggle help
        </pre>
      </div>
    </div>
  )
}

export default HelpOverlay
