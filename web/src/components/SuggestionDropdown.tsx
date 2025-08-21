import React, { useState, useEffect } from 'react'

type Suggestion = {
  value: string
  count?: number
  last_used?: string
  color?: string
  confidence?: number
  origin?: 'db' | 'ai'
  db_known?: boolean
}

type Props = {
  fieldType: 'tag' | 'source' | 'context'
  query: string
  onSelect: (value: string) => void
  visible: boolean
  onClose: () => void
  externalSuggestions?: Suggestion[]
  loading?: boolean
}

const SuggestionDropdown: React.FC<Props> = ({ fieldType, query, onSelect, visible, onClose, externalSuggestions, loading: loadingProp }) => {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)

  useEffect(() => {
    if (!visible) {
      setSuggestions([])
      setSelectedIndex(-1)
      return
    }

    const fetchSuggestions = async () => {
      if (externalSuggestions && externalSuggestions.length >= 0) {
        setSuggestions(externalSuggestions)
        setSelectedIndex(-1)
        setLoading(!!loadingProp)
        return
      }
      setLoading(true)
      try {
        const queryParam = query.trim() ? `query=${encodeURIComponent(query)}&` : ''
        const response = await fetch(`/api/suggestions/${fieldType}?${queryParam}limit=5`)
        const data = await response.json()
        setSuggestions(data.suggestions || [])
        setSelectedIndex(-1)
      } catch (error) {
        console.error('Failed to fetch suggestions:', error)
        setSuggestions([])
        setSelectedIndex(-1)
      } finally {
        setLoading(false)
      }
    }

    const debounceTimer = setTimeout(fetchSuggestions, 300)
    return () => clearTimeout(debounceTimer)
  }, [fieldType, query, visible])

  useEffect(() => {
    if (!visible) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (suggestions.length === 0) return

      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex(prev => prev < suggestions.length - 1 ? prev + 1 : 0)
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex(prev => prev > 0 ? prev - 1 : suggestions.length - 1)
      } else if (e.key === 'Enter' || (e.altKey && e.key === 'ArrowRight')) {
        e.preventDefault()
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          onSelect(suggestions[selectedIndex].value)
          onClose()
        }
      } else if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [visible, suggestions, selectedIndex, onSelect, onClose])

  if (!visible) {
    return null
  }

  return (
    <div className="suggestion-dropdown">
      {(loading || loadingProp) ? (
        <div className="suggestion-item loading">Loading...</div>
      ) : (
        (suggestions || []).length === 0 ? (
          <div className="suggestion-item empty">No suggestions</div>
        ) : (
          suggestions.map((suggestion, index) => (
            <div
              key={index}
              className={`suggestion-item ${index === selectedIndex ? 'selected' : ''}`}
              onClick={() => {
                onSelect(suggestion.value)
                onClose()
              }}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <span className="suggestion-value">{suggestion.value}</span>
              {typeof suggestion.confidence === 'number' && (
                <span className="suggestion-meta">{Math.round(suggestion.confidence * 100)}%</span>
              )}
              {typeof suggestion.count === 'number' && suggestion.count > 0 && (
                <span className="suggestion-meta">({suggestion.count})</span>
              )}
            </div>
          ))
        )
      )}
    </div>
  )
}

export default SuggestionDropdown
