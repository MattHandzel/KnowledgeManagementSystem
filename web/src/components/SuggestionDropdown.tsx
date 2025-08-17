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
}

const SuggestionDropdown: React.FC<Props> = ({ fieldType, query, onSelect, visible, onClose }) => {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!visible || !query.trim()) {
      setSuggestions([])
      return
    }

    const fetchSuggestions = async () => {
      setLoading(true)
      try {
        const response = await fetch(`/api/suggestions/${fieldType}?query=${encodeURIComponent(query)}&limit=5`)
        const data = await response.json()
        setSuggestions(data.suggestions || [])
      } catch (error) {
        console.error('Failed to fetch suggestions:', error)
        setSuggestions([])
      } finally {
        setLoading(false)
      }
    }

    const debounceTimer = setTimeout(fetchSuggestions, 300)
    return () => clearTimeout(debounceTimer)
  }, [fieldType, query, visible])

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
            className="suggestion-item"
            onClick={() => {
              onSelect(suggestion.value)
              onClose()
            }}
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
