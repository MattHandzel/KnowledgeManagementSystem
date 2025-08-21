import React, { useState, KeyboardEvent } from 'react'
import SuggestionDropdown from './SuggestionDropdown'

type Props = {
  value: string
  onChange: (value: string) => void
  placeholder: string
  label: string
  fieldType: 'tag' | 'source'
  aiSuggestions?: { value: string; confidence?: number; db_known?: boolean }[]
  loading?: boolean
  content?: string
}

const EntityChips: React.FC<Props> = ({ value, onChange, placeholder, label, fieldType, aiSuggestions, loading, content }) => {
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [editValue, setEditValue] = useState('')

  const [inputValue, setInputValue] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const normalizeVal = (v: string) => {
    const x = v.trim()
    if (!x) return x
    if (fieldType === 'source') {
      return x.toLowerCase().replace(/[^a-z0-9\s-]/g, '').replace(/[\s_]+/g, '-').replace(/-+/g, '-').replace(/^-+|-+$/g, '')
    }
    const lower = x.toLowerCase()
    if (lower.endsWith('ies') && lower.length > 3) return lower.slice(0, -3) + 'y'
    if (lower.endsWith('ses') && lower.length > 3) return lower.slice(0, -2)
    if (lower.endsWith('s') && !lower.endsWith('ss')) return lower.slice(0, -1)
    return lower
  }
  const aiMap = new Map((aiSuggestions || []).map(s => [s.value.toLowerCase(), s]))

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
  
  const addEntity = async () => {
    const trimmed = inputValue.trim()
    if (trimmed) {
      const normalized = normalizeVal(trimmed)
      if (!entities.map(e => e.toLowerCase()).includes(normalized.toLowerCase())) {
        const newEntities = [...entities, normalized]
        onChange(newEntities.join(', '))
        const meta = aiMap.get(normalized.toLowerCase())
        if (meta && content) {
          try {
            await fetch('/api/ai/feedback', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                content,
                field_type: fieldType,
                original_value: normalized,
                action: 'accepted',
                confidence: meta.confidence ?? null,
                final_value: normalized
              })
            })
          } catch {}
        }
      }
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
      console.error('Failed to check suggestion existence:', error)
      setInputColor('')
    }
  }
  
  const sendFeedback = async (original: string, action: 'accepted' | 'declined' | 'edited', finalValue?: string) => {
    if (!content) return
    const meta = aiMap.get(original.toLowerCase()) || (finalValue ? aiMap.get(finalValue.toLowerCase()) : undefined)
    try {
      await fetch('/api/ai/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content,
          field_type: fieldType,
          original_value: original,
          action,
          final_value: finalValue,
          confidence: meta?.confidence ?? null
        })
      })
    } catch {}
  }

  const removeEntity = (index: number) => {
    const val = entities[index]
    const newEntities = entities.filter((_, i) => i !== index)
    onChange(newEntities.join(', '))
    if (aiMap.has(val.toLowerCase())) {
      sendFeedback(val, 'declined')
    }
  }
  
  return (
    <div className="entity-chips">
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
            onSelect={async (value) => {
              const trimmed = value.trim()
              if (trimmed) {
                const normalized = normalizeVal(trimmed)
                if (!entities.map(e => e.toLowerCase()).includes(normalized.toLowerCase())) {
                  const newEntities = [...entities, normalized]
                  onChange(newEntities.join(', '))
                  await sendFeedback(normalized, 'accepted', normalized)
                }
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
            externalSuggestions={aiSuggestions}
            loading={loading}
          />
        </div>
        {entities.length > 0 && (
          <div className="chips-row">
            {entities.map((entity, index) => (
              <span key={index} className="chip">
                {editingIndex === index ? (
                  <input
                    type="text"
                    value={editValue}
                    autoFocus
                    onChange={(e) => setEditValue(e.target.value)}
                    onBlur={() => {
                      const val = normalizeVal(editValue)
                      const updated = entities.map((e, i) => (i === index ? val : e))
                      onChange(updated.join(', '))
                      if (aiMap.has(entity.toLowerCase())) {
                        if (val !== entity) {
                          sendFeedback(entity, 'edited', val)
                        } else {
                          sendFeedback(entity, 'accepted', val)
                        }
                      }
                      setEditingIndex(null)
                      setEditValue('')
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        (e.target as HTMLInputElement).blur()
                      } else if (e.key === 'Escape') {
                        setEditingIndex(null)
                        setEditValue('')
                      }
                    }}
                    className="chip-input-inline"
                  />
                ) : (
                  <>
                    <span onClick={() => { setEditingIndex(index); setEditValue(entity) }} style={{ cursor: 'text' }}>{entity}</span>
                    <button 
                      type="button" 
                      onClick={() => removeEntity(index)}
                      className="chip-remove"
                    >
                      ×
                    </button>
                  </>
                )}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default EntityChips
