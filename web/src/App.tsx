import React, { useEffect, useState } from 'react'
import CaptureForm from './components/CaptureForm'
import ModalityBar from './components/ModalityBar'
import ClipboardPreview from './components/ClipboardPreview'
import AudioRecorder from './components/AudioRecorder'
import HelpOverlay from './components/HelpOverlay'

type Config = {
  vault: { path: string; capture_dir: string; media_dir: string }
  ui?: { clipboard_poll_ms?: number; show_help?: boolean }
  capture?: Record<string, unknown>
  theme?: { mode?: string; accent_color?: string; accent_hover?: string; accent_shadow?: string }
  mode?: string
  is_dev?: boolean
}

const App: React.FC = () => {
  const [config, setConfig] = useState<Config | null>(null)
  const [content, setContent] = useState('')
  const [context, setContext] = useState('')
  const [tags, setTags] = useState('')
  const [sources, setSources] = useState('')
  const [modalities, setModalities] = useState<string[]>(['text'])
  const [help, setHelp] = useState(false)
  const [saving, setSaving] = useState(false)
  const [savedTo, setSavedTo] = useState<string | null>(null)
  const [mediaFiles, setMediaFiles] = useState<File[]>([])
  const [popup, setPopup] = useState<{type: 'success' | 'error', message: string} | null>(null)

  useEffect(() => {
    fetch('/api/config').then(r => r.json()).then(config => {
      setConfig(config)
      if (config.theme) {
        const root = document.documentElement
        if (config.theme.accent_color) root.style.setProperty('--accent-color', config.theme.accent_color)
        if (config.theme.accent_hover) root.style.setProperty('--accent-hover', config.theme.accent_hover)
        if (config.theme.accent_shadow) root.style.setProperty('--accent-shadow', config.theme.accent_shadow)
        
        if (config.theme.mode === 'dark') {
          root.setAttribute('data-theme', 'dark')
        } else {
          root.removeAttribute('data-theme')
        }
      }
    }).catch(() => setConfig({ vault: { path: '', capture_dir: '', media_dir: '' } }))
  }, [])

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'F1') { e.preventDefault(); setHelp(x => !x) }
      if (e.key === 'Enter' && e.ctrlKey) { 
        e.preventDefault(); 
        handleSave()
      }
      if (e.key === 'Escape') { 
        e.preventDefault(); 
        resetForm()
      }
      if (e.ctrlKey && /^[1-9]$/.test(e.key)) {
        e.preventDefault()
        const idx = parseInt(e.key, 10) - 1
        toggleModalityByIndex(idx)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [modalities, content, context, tags, sources])

  const toggleModality = (m: string) => {
    setModalities(prev => prev.includes(m) ? prev.filter(x => x !== m) : [...prev, m])
  }
  const toggleModalityByIndex = (i: number) => {
    const all = ['text','clipboard','screenshot','audio','system-audio']
    if (i >= 0 && i < all.length) toggleModality(all[i])
  }
  const resetForm = () => {
    setContent('')
    setContext('')
    setTags('')
    setSources('')
    setModalities(['text'])
    setMediaFiles([])
  }
  const onFiles = (files: FileList | null) => {
    if (!files) return
    setMediaFiles(Array.from(files))
    if (!modalities.includes('files')) setModalities([...modalities, 'files'])
  }
  const onScreenshot = async () => {
    try {
      const response = await fetch('/api/screenshot', { method: 'POST' })
      const data = await response.json()
      if (data.success && data.path) {
        const screenshotMeta = { path: data.path, type: 'screenshot', name: `screenshot_${Date.now()}.png` }
        setMediaFiles(prev => [...prev, screenshotMeta as any])
        if (!modalities.includes('screenshot')) setModalities([...modalities, 'screenshot'])
      }
    } catch (error) {
      console.error('Screenshot failed:', error)
    }
  }

  const onAudioReady = (file: File) => {
    setMediaFiles(prev => [...prev, file])
    if (!modalities.includes('audio')) setModalities([...modalities, 'audio'])
  }

  const onSystemAudioReady = (file: File) => {
    setMediaFiles(prev => [...prev, file])
    if (!modalities.includes('system-audio')) setModalities([...modalities, 'system-audio'])
  }
  const handleSave = async () => {
    console.log('DEBUG: onSave called with content:', content)
    console.log('DEBUG: onSave called with context:', context)
    console.log('DEBUG: onSave called with tags:', tags)
    setSaving(true)
    try {
      const fd = new FormData()
      fd.append('content', content)
      fd.append('context', context)
      fd.append('tags', tags)
      fd.append('sources', sources)
      fd.append('modalities', modalities.join(','))
      
      if (modalities.includes('clipboard')) {
        try {
          const clipResponse = await fetch('/api/clipboard')
          const clipData = await clipResponse.json()
          fd.append('clipboard', clipData.content || '')
        } catch (error) {
          console.error('Failed to get clipboard content:', error)
        }
      }
      
      const now = new Date()
      const d = now.toISOString().slice(0,10)
      fd.append('created_date', d)
      fd.append('last_edited_date', d)
      mediaFiles.forEach(f => {
        if ((f as any).path && (f as any).type) {
          fd.append('screenshot_path', (f as any).path)
          fd.append('screenshot_type', (f as any).type)
        } else {
          fd.append('media', f, f.name)
        }
      })
      const r = await fetch('/api/capture', { method: 'POST', body: fd })
      const j = await r.json()
      setSavedTo(j.saved_to || null)
      setPopup({ type: 'success', message: `Saved to: ${j.saved_to}` })
      resetForm()
      if (j.saved_to) {
        setTimeout(() => setSavedTo(null), 4000)
      }
    } catch (error) {
      console.error('Save failed:', error)
      setPopup({ type: 'error', message: `Save failed: ${error instanceof Error ? error.message : 'Unknown error'}` })
      setSavedTo(null)
    } finally {
      setSaving(false)
    }
  }

  const pollMs = config?.ui?.clipboard_poll_ms || 200

  useEffect(() => {
    if (popup) {
      const timer = setTimeout(() => setPopup(null), 5000)
      return () => clearTimeout(timer)
    }
  }, [popup])


  return (
    <div className="container">
      {config?.is_dev && (
        <div className="dev-banner">
          🚧 DEV MODE 🚧
        </div>
      )}
      <ModalityBar modalities={modalities} onToggle={toggleModality} onScreenshot={onScreenshot} />
      <CaptureForm
        content={content} setContent={setContent}
        context={context} setContext={setContext}
        tags={tags} setTags={setTags}
        sources={sources} setSources={setSources}
        onFiles={onFiles}
        saving={saving}
        onSave={handleSave}
      />
      {modalities.includes('clipboard') && <ClipboardPreview intervalMs={pollMs} />}
      {modalities.includes('audio') && (
        <AudioRecorder 
          onAudioReady={(file) => {
            setMediaFiles(prev => [...prev, file])
          }} 
          systemAudio={false}
        />
      )}
      {modalities.includes('system-audio') && (
        <AudioRecorder 
          onAudioReady={(file) => {
            setMediaFiles(prev => [...prev, file])
          }} 
          systemAudio={true}
        />
      )}
      {help && <HelpOverlay onClose={() => setHelp(false)} />}
      {savedTo && <div className="saved">Saved to {savedTo}</div>}
      {popup && (
        <div className={`popup ${popup.type}`} onClick={() => setPopup(null)}>
          {popup.message}
        </div>
      )}
    </div>
  )
}

export default App
