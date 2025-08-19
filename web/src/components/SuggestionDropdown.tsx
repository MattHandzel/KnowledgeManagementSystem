import React, { useState, useEffect } from 'react'

type Suggestion = {
  value: string
  count: number
  last_used: string
  color: string
}

type Props = {
  fieldType: 'tag' | 'source' | 'context'
  query: string
  onSelect: (value: string) => void
  visible: boolean
  onClose: () => void
  onSelectionChange?: (hasSelection: boolean) => void
}

const SuggestionDropdown: React.FC<Props> = ({ fieldType, query, onSelect, visible, onClose, onSelectionChange }) => {
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

  useEffect(() => {
    if (onSelectionChange) {
      onSelectionChange(selectedIndex >= 0 && selectedIndex < suggestions.length)
    }
  }, [selectedIndex, suggestions.length, onSelectionChange])

  if (!visible || suggestions.length === 0) {
    return null
  }

  return (
    <div className="suggestion-dropdown">
      {loading ? (
        <div className="suggestion-item loading">Loading...</div>
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
            <span className="suggestion-meta">({suggestion.count} uses)</span>
          </div>
        ))
      )}
    </div>
  )
}

export default SuggestionDropdown
