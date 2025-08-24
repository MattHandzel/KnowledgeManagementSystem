import React, { useState, KeyboardEvent } from 'react'
import SuggestionDropdown from './SuggestionDropdown'

type AISuggestion = { value: string; confidence?: number }

type Props = {
  value: string
  onChange: (value: string) => void
  placeholder: string
  label: string
  fieldType: 'tag' | 'source'
  aiSuggestions?: AISuggestion[]
  onAcceptAISuggestion?: (value: string, confidence?: number) => void
  onDeclineAISuggestion?: (value: string, confidence?: number) => void
  generating?: boolean
  devRegenerate?: (() => void) | null
}

const EntityChips: React.FC<Props> = ({ value, onChange, placeholder, label, fieldType, aiSuggestions = [], onAcceptAISuggestion, onDeclineAISuggestion, generating = false, devRegenerate = null }) => {
  const [inputValue, setInputValue] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [inputColor, setInputColor] = useState('')
  const [suggestionSelected, setSuggestionSelected] = useState(false)
  
  const entities = value ? value.split(',').map(s => s.trim()).filter(s => s) : []
  
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      setSuggestionSelected(true)
      return
    }
    
    if (e.key === 'Escape') {
      setSuggestionSelected(false)
      setShowSuggestions(false)
      return
    }
    
    if (e.key === 'Enter' || (e.altKey && e.key === 'ArrowRight')) {
      if (showSuggestions && suggestionSelected) {
        return
      }
      e.preventDefault()
      addEntity()
    } else if (e.key === ',') {
      e.preventDefault()
      addEntity()
    } else if (e.key === 'Backspace' && inputValue === '' && entities.length > 0) {
      removeEntity(entities.length - 1)
    }
  }
  
  const addEntity = () => {
    const trimmed = inputValue.trim()
    if (trimmed && !entities.includes(trimmed)) {
      const newEntities = [...entities, trimmed]
      onChange(newEntities.join(', '))
      setInputValue('')
      setShowSuggestions(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)
    setShowSuggestions(true)
    setSuggestionSelected(false)
    
    if (newValue.trim()) {
      checkValueExists(newValue.trim())
    } else {
      setInputColor('')
    }
  }

  const checkValueExists = async (value: string) => {
    try {
      const response = await fetch(`/api/suggestion-exists/${fieldType}?value=${encodeURIComponent(value)}`)
      const data = await response.json()
      setInputColor(data.exists ? 'var(--text-muted)' : '')
    } catch (error) {
      setInputColor('')
    }
  }
  
  const removeEntity = (index: number) => {
    const newEntities = entities.filter((_, i) => i !== index)
    onChange(newEntities.join(', '))
  }
  
  const acceptAISuggestion = (s: AISuggestion) => {
    if (!s.value) return
    if (!entities.includes(s.value)) {
      const newEntities = [...entities, s.value]
      onChange(newEntities.join(', '))
    }
    if (onAcceptAISuggestion) onAcceptAISuggestion(s.value, s.confidence)
  }

  const editAISuggestion = (s: AISuggestion) => {
    setInputValue(s.value)
  }

  return (
    <div className={`entity-chips ${generating ? 'generating' : ''}`}>
      <label>{label}</label>
      <div className="chips-container">
        <div className="chip-input-container">
          <input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onBlur={() => {
              setTimeout(() => setShowSuggestions(false), 200)
              addEntity()
            }}
            onFocus={() => {
              setShowSuggestions(true)
            }}
            placeholder={entities.length === 0 ? placeholder : ''}
            className="chip-input"
            style={{ color: inputColor }}
          />
          <SuggestionDropdown
            fieldType={fieldType}
            query={inputValue}
            onSelect={(value) => {
              const trimmed = value.trim()
              if (trimmed && !entities.includes(trimmed)) {
                const newEntities = [...entities, trimmed]
                onChange(newEntities.join(', '))
                setInputValue('')
                setShowSuggestions(false)
                setSuggestionSelected(false)
              }
            }}
            visible={showSuggestions}
            onClose={() => {
              setShowSuggestions(false)
              setSuggestionSelected(false)
            }}
          />
        </div>
        {aiSuggestions && aiSuggestions.length > 0 && (
          <div className="chips-row suggested">
            {aiSuggestions.map((s, i) => (
              <span key={`${s.value}-${i}`} className="chip suggested-chip" onDoubleClick={() => editAISuggestion(s)}>
                <span className="chip-label" onClick={() => acceptAISuggestion(s)}>{s.value}</span>
                {typeof s.confidence === 'number' && <span className="chip-conf"> {(s.confidence * 100).toFixed(0)}%</span>}
                <button
                  type="button"
                  onClick={() => { if (onDeclineAISuggestion) onDeclineAISuggestion(s.value, s.confidence) }}
                  className="chip-remove"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
        {entities.length > 0 && (
          <div className="chips-row">
            {entities.map((entity, index) => (
              <span key={index} className="chip">
                {entity}
                <button 
                  type="button" 
                  onClick={() => removeEntity(index)}
                  className="chip-remove"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
        {devRegenerate && (
          <div className="ai-actions">
            <button type="button" onClick={() => devRegenerate()}>Regenerate</button>
          </div>
        )}
      </div>
    </div>
  )
}

export default EntityChips
