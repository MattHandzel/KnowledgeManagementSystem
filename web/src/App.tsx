import React, { useEffect, useMemo, useRef, useState } from 'react'
import CaptureForm from './components/CaptureForm'
import ModalityBar from './components/ModalityBar'
import ClipboardPreview from './components/ClipboardPreview'
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
  const ctrlDown = useRef(false)

  useEffect(() => {
    fetch('/api/config').then(r => r.json()).then(setConfig).catch(() => setConfig({ vault: { path: '', capture_dir: '', media_dir: '' } }))
  }, [])

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Control') ctrlDown.current = true
      if (e.key === 'F1') { e.preventDefault(); setHelp(x => !x) }
      if (e.key.toLowerCase() === 's' && e.ctrlKey) { e.preventDefault(); onSave() }
      if (e.key === 'Escape') { e.preventDefault(); resetForm() }
      if (ctrlDown.current && /^[1-9]$/.test(e.key)) {
        e.preventDefault()
        const idx = parseInt(e.key, 10) - 1
        toggleModalityByIndex(idx)
      }
    }
    const onKeyUp = (e: KeyboardEvent) => {
      if (e.key === 'Control') ctrlDown.current = false
    }
    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('keyup', onKeyUp)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('keyup', onKeyUp)
    }
  }, [modalities])

  const toggleModality = (m: string) => {
    setModalities(prev => prev.includes(m) ? prev.filter(x => x !== m) : [...prev, m])
  }
  const toggleModalityByIndex = (i: number) => {
    const all = ['text','clipboard','screenshot','audio','files']
    if (i >= 0 && i < all.length) toggleModality(all[i])
  }
  const resetForm = () => {
    setContent('')
    setContext('')
    setTags('')
    setSources('')
    setModalities(['text'])
    setMediaFiles([])
    setSavedTo(null)
  }
  const onFiles = (files: FileList | null) => {
    if (!files) return
    setMediaFiles(Array.from(files))
    if (!modalities.includes('files')) setModalities([...modalities, 'files'])
  }
  const onScreenshot = async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: true })
      const track = stream.getVideoTracks()[0]
      const imageCapture = new (window as any).ImageCapture(track)
      const blob = await imageCapture.grabFrame().then((bitmap: ImageBitmap) => {
        const canvas = document.createElement('canvas')
        canvas.width = bitmap.width
        canvas.height = bitmap.height
        const ctx2 = canvas.getContext('2d')!
        ctx2.drawImage(bitmap, 0, 0)
        return new Promise<Blob>(res => canvas.toBlob(b => res(b as Blob), 'image/png'))
      })
      const file = new File([blob], `screenshot_${Date.now()}.png`, { type: 'image/png' })
      setMediaFiles(prev => [...prev, file])
      if (!modalities.includes('screenshot')) setModalities([...modalities, 'screenshot'])
      track.stop()
      stream.getTracks().forEach(t => t.stop())
    } catch {}
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
    } catch {
      setSavedTo(null)
    } finally {
      setSaving(false)
    }
  }

  const pollMs = config?.ui?.clipboard_poll_ms || 200

  return (
    <div className="container">
      <h1>KMS Capture</h1>
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
      {help && <HelpOverlay onClose={() => setHelp(false)} />}
      {savedTo && <div className="saved">Saved to {savedTo}</div>}
    </div>
  )
}

export default App
