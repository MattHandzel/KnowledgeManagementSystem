import React, { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
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
  const [showMarkdownPreview, setShowMarkdownPreview] = useState(false)

  useEffect(() => {
    loadPersistentValues()
  }, [])

  const loadPersistentValues = async () => {
    try {
      const [tagsRes, sourcesRes, contextRes] = await Promise.all([
        fetch('/api/suggestions/tag?limit=1'),
        fetch('/api/suggestions/source?limit=1'),
        fetch('/api/suggestions/context?limit=1')
      ])
      
      const [tagsData, sourcesData, contextData] = await Promise.all([
        tagsRes.json(),
        sourcesRes.json(),
        contextRes.json()
      ])
      
      if (tagsData.suggestions?.length > 0 && !p.tags) {
        p.setTags(tagsData.suggestions[0].value)
      }
      if (sourcesData.suggestions?.length > 0 && !p.sources) {
        p.setSources(sourcesData.suggestions[0].value)
      }
      if (contextData.suggestions?.length > 0 && !p.context) {
        p.setContext(contextData.suggestions[0].value)
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
    if (p.context.trim()) {
      setShowContextSuggestions(true)
    }
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

  return (
    <div className="form">
      <div className="content-container">
        <div className="content-header">
          <button 
            type="button"
            onClick={() => setShowMarkdownPreview(!showMarkdownPreview)}
            className="markdown-toggle"
          >
            {showMarkdownPreview ? 'Edit' : 'Preview'}
          </button>
        </div>
        {showMarkdownPreview ? (
          <div className="markdown-preview">
            <ReactMarkdown>{p.content || '*No content to preview*'}</ReactMarkdown>
          </div>
        ) : (
          <textarea 
            value={p.content} 
            onChange={e => p.setContent(e.target.value)} 
            rows={10}
            placeholder="Enter your content here... Use **bold** and _italic_ markdown formatting"
          />
        )}
      </div>
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
