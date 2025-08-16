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

  useEffect(() => {
    fetch('/api/config').then(r => r.json()).then(setConfig).catch(() => setConfig({ vault: { path: '', capture_dir: '', media_dir: '' } }))
  }, [])

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'F1') { e.preventDefault(); setHelp(x => !x) }
      if (e.key.toLowerCase() === 's' && e.ctrlKey) { e.preventDefault(); onSave() }
      if (e.key === 'Escape') { e.preventDefault(); resetForm() }
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
  }, [modalities])

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
      if (data.success) {
        const file = new File([new Blob()], `screenshot_${Date.now()}.png`, { type: 'image/png' })
        setMediaFiles(prev => [...prev, file])
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
  const onSave = async () => {
    setSaving(true)
    try {
      const fd = new FormData()
      fd.append('content', content)
      fd.append('context', context)
      fd.append('tags', tags)
      fd.append('sources', sources)
      fd.append('modalities', modalities.join(','))
      const now = new Date()
      const d = now.toISOString().slice(0,10)
      fd.append('created_date', d)
      fd.append('last_edited_date', d)
      mediaFiles.forEach(f => fd.append('media', f, f.name))
      const r = await fetch('/api/capture', { method: 'POST', body: fd })
      const j = await r.json()
      setSavedTo(j.saved_to || null)
      resetForm()
      if (j.saved_to) {
        setTimeout(() => setSavedTo(null), 4000)
      }
    } catch {
      setSavedTo(null)
    } finally {
      setSaving(false)
    }
  }

  const pollMs = config?.ui?.clipboard_poll_ms || 200

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>KMS Capture</h1>
        <button aria-label="Help" onClick={() => setHelp(true)}>Help</button>
      </div>
      <ModalityBar modalities={modalities} onToggle={toggleModality} onScreenshot={onScreenshot} />
      <CaptureForm
        content={content} setContent={setContent}
        context={context} setContext={setContext}
        tags={tags} setTags={setTags}
        sources={sources} setSources={setSources}
        onFiles={onFiles}
        saving={saving}
        onSave={onSave}
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
    </div>
  )
}

export default App
