import React, { useState, useEffect, useRef } from 'react'
import EntityChips from './EntityChips'
import SuggestionDropdown from './SuggestionDropdown'
import PublicToggle from './PublicToggle'

type AISuggestion = { value: string; confidence?: number }

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
  const [aiTagSuggestions, setAiTagSuggestions] = useState<AISuggestion[]>([])
  const [aiSourceSuggestions, setAiSourceSuggestions] = useState<AISuggestion[]>([])
  const [generatingTags, setGeneratingTags] = useState(false)
  const [generatingSources, setGeneratingSources] = useState(false)
  const [dev, setDev] = useState(false)
  const [aiReady, setAiReady] = useState(false)
  const [isPublic, setIsPublic] = useState(false)
  const aiConfigRef = useRef<{ on_blur: boolean; interval_ms: number; dev_regen: boolean } | null>(null)
  const lastContentHash = useRef<string>('')

  useEffect(() => {
    loadPersistentValues()
  }, [])

  // Initialize public toggle based on existing tags
  useEffect(() => {
    const tagList = p.tags.split(',').map(t => t.trim()).filter(t => t)
    setIsPublic(tagList.includes('public'))
  }, [p.tags])

  // Handle public toggle changes
  const handlePublicToggle = (newIsPublic: boolean) => {
    setIsPublic(newIsPublic)
    
    const tagList = p.tags.split(',').map(t => t.trim()).filter(t => t)
    
    if (newIsPublic) {
      // Add public tag if not already present
      if (!tagList.includes('public')) {
        const newTags = [...tagList, 'public'].join(', ')
        p.setTags(newTags)
      }
    } else {
      // Remove public tag if present
      const filteredTags = tagList.filter(t => t !== 'public')
      p.setTags(filteredTags.join(', '))
    }
  }

  const loadPersistentValues = async () => {
    try {
      const configRes = await fetch('/api/config')
      const config = await configRes.json()
      setDev(!!config?.is_dev)
      const ai = config?.ai || {}
      const triggers = ai?.triggers || {}
      aiConfigRef.current = { on_blur: !!triggers.on_blur, interval_ms: triggers.interval_ms || 5000, dev_regen: !!(ai?.behavior?.dev_enable_regenerate_button) }
      setAiReady(true)
      
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
    }
  }

  useEffect(() => {
    if (!aiReady || !aiConfigRef.current) return
    const intervalMs = aiConfigRef.current.interval_ms
    let t: number | undefined
    const onFocus = () => {
      if (intervalMs > 0) {
        if (t) window.clearInterval(t)
        t = window.setInterval(() => {
          if (document.activeElement && (document.activeElement as HTMLElement).tagName.toLowerCase() === 'textarea') {
            triggerAISuggestions()
          }
        }, intervalMs)
      }
    }
    const onBlur = () => {
      if (t) window.clearInterval(t)
      if (aiConfigRef.current?.on_blur) triggerAISuggestions()
    }
    window.addEventListener('focus', onFocus, true)
    window.addEventListener('blur', onBlur, true)
    onFocus()
    return () => {
      window.removeEventListener('focus', onFocus, true)
      window.removeEventListener('blur', onBlur, true)
      if (t) window.clearInterval(t)
    }
  }, [p.content, aiReady])

  const computeHash = (s: string) => {
    try {
      const enc = new TextEncoder().encode(s)
      let h = 0
      for (let i = 0; i < enc.length; i++) {
        h = (h * 31 + enc[i]) >>> 0
      }
      return String(h)
    } catch {
      return String(s.length)
    }
  }

  const triggerAISuggestions = async () => {
    const c = (p.content || '').trim()
    if (!c) return
    const h = computeHash(c)
    if (h === lastContentHash.current) return
    lastContentHash.current = h
    setGeneratingTags(true)
    try {
      const tagRes = await fetch(`/api/ai-suggestions/tag?limit=8&content=${encodeURIComponent(c)}`)
      const tagJson = await tagRes.json()
      const ai = tagJson.ai || []
      setAiTagSuggestions(ai)
    } catch (e) {
      setAiTagSuggestions([])
    } finally {
      setGeneratingTags(false)
    }
    setGeneratingSources(true)
    try {
      const srcRes = await fetch(`/api/ai-suggestions/source?limit=8&content=${encodeURIComponent(c)}`)
      const srcJson = await srcRes.json()
      const ai = srcJson.ai || []
      setAiSourceSuggestions(ai)
    } catch (e) {
      setAiSourceSuggestions([])
    } finally {
      setGeneratingSources(false)
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
      setContextColor('')
    }
  }

  const onAcceptAI = async (field: 'tag' | 'source', value: string, confidence?: number) => {
    try {
      const fd = new FormData()
      fd.append('field_type', field)
      fd.append('value', value)
      fd.append('action', 'accepted')
      if (typeof confidence === 'number') fd.append('confidence', String(confidence))
      fd.append('content_hash', lastContentHash.current)
      await fetch('/api/ai-suggestions/feedback', { method: 'POST', body: fd })
    } catch {}
  }

  const onDeclineAI = async (field: 'tag' | 'source', value: string, confidence?: number) => {
    try {
      const fd = new FormData()
      fd.append('field_type', field)
      fd.append('value', value)
      fd.append('action', 'declined')
      if (typeof confidence === 'number') fd.append('confidence', String(confidence))
      fd.append('content_hash', lastContentHash.current)
      await fetch('/api/ai-suggestions/feedback', { method: 'POST', body: fd })
    } catch {}
    if (field === 'tag') setAiTagSuggestions(prev => prev.filter(x => x.value !== value))
    else setAiSourceSuggestions(prev => prev.filter(x => x.value !== value))
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
        onBlur={() => { if (aiConfigRef.current?.on_blur) triggerAISuggestions() }}
        rows={8} 
        placeholder="write your capture content here..."
      />
      <div className={`context-input-container`}>
        <input 
          value={p.context} 
          onChange={handleContextChange}
          onFocus={handleContextFocus}
          onBlur={() => setTimeout(() => setShowContextSuggestions(false), 250)}
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
          onChange={(v) => { p.setSources(v) }}
          placeholder="Sources"
          label=""
          fieldType="source"
          aiSuggestions={aiSourceSuggestions}
          generating={generatingSources}
          devRegenerate={dev ? (() => triggerAISuggestions()) : null}
          onAcceptAISuggestion={(value, conf) => { onAcceptAI('source', value, conf) }}
          onDeclineAISuggestion={(value, conf) => { onDeclineAI('source', value, conf) }}
        />
        <div className="tags-public-container">
          <EntityChips
            value={p.tags}
            onChange={(v) => { p.setTags(v) }}
            placeholder="Tags"
            label=""
            fieldType="tag"
            aiSuggestions={aiTagSuggestions}
            generating={generatingTags}
            devRegenerate={dev ? (() => triggerAISuggestions()) : null}
            onAcceptAISuggestion={(value, conf) => { onAcceptAI('tag', value, conf) }}
            onDeclineAISuggestion={(value, conf) => { onDeclineAI('tag', value, conf) }}
          />
          <PublicToggle
            isPublic={isPublic}
            onToggle={handlePublicToggle}
          />
        </div>
      </div>
    </div>
  )
}

export default CaptureForm
