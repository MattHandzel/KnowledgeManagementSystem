import React, { useState, useEffect, useRef } from 'react'
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
  const [aiTags, setAiTags] = useState<{ value: string; confidence?: number; db_known?: boolean }[]>([])
  const [aiSources, setAiSources] = useState<{ value: string; confidence?: number; db_known?: boolean }[]>([])
  const [aiLoadingTags, setAiLoadingTags] = useState(false)
  const [aiLoadingSources, setAiLoadingSources] = useState(false)
  const lastHashRef = useRef<string | null>(null)

  const [contextColor, setContextColor] = useState('')

  useEffect(() => {
    loadPersistentValues()
    debounceContent()
  }, [])

  useEffect(() => {
    debounceContent()
  }, [p.content])

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
  const debounceContent = () => {
    const content = p.content || ''
    const hash = String(content.length) + (content.slice(0, 32) || '')
    if (!content.trim()) {
      setAiTags([])
      setAiSources([])
      setAiLoadingTags(false)
      setAiLoadingSources(false)
      lastHashRef.current = null
      return
    }
    if (lastHashRef.current === hash) return
    lastHashRef.current = hash
    const run = async () => {
      setAiLoadingTags(true)
      try {
        const r1 = await fetch(`/api/suggestions/tag?limit=5&content=${encodeURIComponent(content)}`)
        const j1 = await r1.json()
        setAiTags(j1.suggestions || [])
      } catch (e) {
        setAiTags([])
      } finally {
        setAiLoadingTags(false)
      }
      setAiLoadingSources(true)
      try {
        const r2 = await fetch(`/api/suggestions/source?limit=5&content=${encodeURIComponent(content)}`)
        const j2 = await r2.json()
        setAiSources(j2.suggestions || [])
      } catch (e) {
        setAiSources([])
      } finally {
        setAiLoadingSources(false)
      }
    }
    setTimeout(run, 800)
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
        onChange={e => { p.setContent(e.target.value); }}
        onBlur={() => debounceContent()}
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
          aiSuggestions={aiSources}
          loading={aiLoadingSources}
          content={p.content}
        />
        <EntityChips
          value={p.tags}
          onChange={p.setTags}
          placeholder="Tags"
          label=""
          fieldType="tag"
          aiSuggestions={aiTags}
          loading={aiLoadingTags}
          content={p.content}
        />
      </div>
    </div>
  )
}

export default CaptureForm
