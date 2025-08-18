import React, { useState, KeyboardEvent } from 'react'
import SuggestionDropdown from './SuggestionDropdown'

type Props = {
  value: string
  onChange: (value: string) => void
  placeholder: string
  label: string
  fieldType: 'tag' | 'source'
}

const EntityChips: React.FC<Props> = ({ value, onChange, placeholder, label, fieldType }) => {
  const [inputValue, setInputValue] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [inputColor, setInputColor] = useState('')
  
  const entities = value ? value.split(',').map(s => s.trim()).filter(s => s) : []
  
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === ',' || e.key === 'Enter') {
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
      console.error('Failed to check suggestion existence:', error)
      setInputColor('')
    }
  }
  
  const removeEntity = (index: number) => {
    const newEntities = entities.filter((_, i) => i !== index)
    onChange(newEntities.join(', '))
  }
  
  return (
    <div className="entity-chips">
      <label>{label}</label>
      <div className="chips-container">
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
              }
            }}
            visible={showSuggestions}
            onClose={() => setShowSuggestions(false)}
          />
        </div>
      </div>
    </div>
  )
}

export default EntityChips
