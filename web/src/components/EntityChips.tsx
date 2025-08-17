import React, { useState, KeyboardEvent } from 'react'

type Props = {
  value: string
  onChange: (value: string) => void
  placeholder: string
  label: string
}

const EntityChips: React.FC<Props> = ({ value, onChange, placeholder, label }) => {
  const [inputValue, setInputValue] = useState('')
  
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
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={addEntity}
          placeholder={entities.length === 0 ? placeholder : ''}
          className="chip-input"
        />
      </div>
    </div>
  )
}

export default EntityChips
