import React, { useState, useEffect } from 'react'
import EntityChips from './EntityChips'
import SuggestionDropdown from './SuggestionDropdown'

type Props = {
  content: string
  setContent: (v: string) => void
  context: string
  setContext: (v: string) => void
  tags: string
  setTags: (v: string) => void
  sources: string
  setSources: (v: string) => void
  onFiles: (f: FileList | null) => void
  saving: boolean
  onSave: () => void
}

const CaptureForm: React.FC<Props> = (p) => {
  const [showContextSuggestions, setShowContextSuggestions] = useState(false)
  const [contextColor, setContextColor] = useState('')

  useEffect(() => {
    loadPersistentValues()
  }, [])

  const loadPersistentValues = async () => {
    try {
      const configRes = await fetch('/api/config')
      const config = await configRes.json()
      
      if (!config.capture?.restore_previous_fields) {
        return
      }
      
      const recentRes = await fetch('/api/recent-values')
      const recentData = await recentRes.json()
      const recentValues = recentData.recent_values || {}
      
      if (recentValues.tags?.length > 0 && !p.tags) {
        p.setTags(recentValues.tags.join(', '))
      }
      
      if (recentValues.sources?.length > 0 && !p.sources) {
        p.setSources(recentValues.sources.join(', '))
      }
      
      if (recentValues.context?.length > 0 && !p.context) {
        p.setContext(recentValues.context[0])
      }
    } catch (error) {
      console.error('Failed to load persistent values:', error)
    }
  }

  const handleContextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    p.setContext(newValue)
    
    if (newValue.trim()) {
      checkContextExists(newValue.trim())
    } else {
      setContextColor('')
    }
  }

  const handleContextFocus = () => {
    setShowContextSuggestions(true)
  }

  const checkContextExists = async (value: string) => {
    try {
      const response = await fetch(`/api/suggestion-exists/context?value=${encodeURIComponent(value)}`)
      const data = await response.json()
      setContextColor(data.exists ? 'var(--text-muted)' : '')
    } catch (error) {
      console.error('Failed to check context existence:', error)
      setContextColor('')
    }
  }

  const renderInlineMarkdown = (text: string) => {
    if (!text) return ''
    
    return text
      .replace(/\*\*(.*?)\*\*/g, '<span class="md-bold">**$1**</span>')
      .replace(/_(.*?)_/g, '<span class="md-italic">_$1_</span>')
      .replace(/`(.*?)`/g, '<span class="md-code">`$1`</span>')
      .replace(/^# (.*$)/gm, '<span class="md-h1"># $1</span>')
      .replace(/^## (.*$)/gm, '<span class="md-h2">## $1</span>')
      .replace(/^### (.*$)/gm, '<span class="md-h3">### $1</span>')
      .replace(/\n/g, '<br>')
  }

  return (
    <div className="form">
      <textarea 
        value={p.content} 
        onChange={e => p.setContent(e.target.value)} 
        rows={10} 
        placeholder="Content (supports **bold**, _italic_, `code`, # headers)"
      />
      <div className="context-input-container">
        <input 
          value={p.context} 
          onChange={handleContextChange}
          onFocus={handleContextFocus}
          onBlur={() => setTimeout(() => setShowContextSuggestions(false), 200)}
          placeholder="Context"
          className=""
          style={{ color: contextColor }}
        />
        <SuggestionDropdown
          fieldType="context"
          query={p.context}
          onSelect={(value) => p.setContext(value)}
          visible={showContextSuggestions}
          onClose={() => setShowContextSuggestions(false)}
        />
      </div>
      <div className="tags-sources-row">
        <EntityChips
          value={p.sources}
          onChange={p.setSources}
          placeholder="Sources"
          label=""
          fieldType="source"
        />
        <EntityChips
          value={p.tags}
          onChange={p.setTags}
          placeholder="Tags"
          label=""
          fieldType="tag"
        />
      </div>
    </div>
  )
}

export default CaptureForm
