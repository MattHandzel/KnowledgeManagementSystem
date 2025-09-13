import React, { useState, KeyboardEvent, useEffect } from 'react'
import SuggestionDropdown from './SuggestionDropdown'

type AISuggestion = { value: string; confidence?: number }

type Props = {
  value: string
  onChange: (value: string) => void
  placeholder: string
  label: string
  fieldType: 'tag' | 'source' | 'alias'
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
  const [suggestionWasClicked, setSuggestionWasClicked] = useState(false)
  
  const entities = value ? value.split(',').map(s => s.trim()).filter(s => s) : []
  
  // Track which entities were suggested by AI vs added by user
  const [aiSuggestedEntities, setAiSuggestedEntities] = useState<Set<string>>(new Set())
  
  // When AI suggestions change, update our tracked set
  useEffect(() => {
    if (aiSuggestions && aiSuggestions.length > 0) {
      const newAiEntities = new Set(aiSuggestions.map(s => s.value))
      setAiSuggestedEntities(prev => new Set([...Array.from(prev), ...Array.from(newAiEntities)]))
    }
  }, [aiSuggestions])
  
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
    } else if (e.key === 'Backspace' && e.ctrlKey) {
      // Clear all entities when Ctrl+Backspace is pressed
      e.preventDefault()
      clearAllEntities()
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
  
  const clearAllEntities = () => {
    onChange('')
  }
  
  const acceptAISuggestion = (s: AISuggestion) => {
    if (!s.value) return
    if (!entities.includes(s.value)) {
      const newEntities = [...entities, s.value]
      onChange(newEntities.join(', '))
    }
    if (onAcceptAISuggestion) onAcceptAISuggestion(s.value)
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
              setTimeout(() => {
                if (!suggestionWasClicked) {
                  addEntity()
                }
                setShowSuggestions(false)
                setSuggestionWasClicked(false) // Reset for next interaction
              }, 200) // Delay to allow click event to register
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
              setSuggestionWasClicked(true)
              const trimmed = value.trim()
              if (trimmed && !entities.includes(trimmed)) {
                const newEntities = [...entities, trimmed]
                onChange(newEntities.join(', '))
              }
              setInputValue('')
              setShowSuggestions(false)
              setSuggestionSelected(false)
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
            {aiSuggestions
              .filter(s => !entities.includes(s.value)) // Filter out suggestions already selected by the user
              // .filter(s => !s.confidence || s.confidence >= 0.9) // Only show suggestions with confidence >= 0.5
              .map((s, i) => (
                <span 
                  key={`${s.value}-${i}`} 
                  className="chip suggested-chip ai-suggestion" 
                  onClick={() => acceptAISuggestion(s)}
                  onDoubleClick={() => editAISuggestion(s)}
                  title={`Accept AI suggestion: "${s.value}"`}
                >
                  <span className="ai-icon">✨</span>
                  <span className="chip-label">{s.value}</span>
                </span>
              ))}
          </div>
        )}
        {entities.length > 0 && (
          <div className="chips-row">
            {entities.map((entity, index) => {
              const isAiSuggested = aiSuggestedEntities.has(entity);
              return (
                <span 
                  key={index} 
                  className={`chip ${isAiSuggested ? 'ai-suggested' : 'user-added'}`}
                  title={isAiSuggested ? 'AI suggested' : `User added. Click to remove "${entity}".`}
                  onClick={() => removeEntity(index)}
                >
                  {isAiSuggested && <span className="ai-icon">✨</span>}
                  {entity}
                </span>
              );
            })}
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
