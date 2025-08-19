import React, { useEffect, useState } from 'react'
import CaptureForm from './components/CaptureForm'
import ModalityBar from './components/ModalityBar'
import ClipboardPreview from './components/ClipboardPreview'
import AudioRecorder from './components/AudioRecorder'
import HelpOverlay from './components/HelpOverlay'
import { isNative, nativeSave, pickVaultDirectory, getVaultInfo } from './shared/platform'
import { formatCaptureMarkdown } from './shared/serialization'

type Config = {
  vault: { path: string; capture_dir: string; media_dir: string }
  ui?: { clipboard_poll_ms?: number; show_help?: boolean; use_modality_icons?: boolean }
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
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [mediaFiles, setMediaFiles] = useState<File[]>([])
  const [vaultInfo, setVaultInfo] = useState<{ captureDirAbs: string; mediaDirAbs: string } | null>(null)

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
  useEffect(() => {
    if (isNative()) {
      getVaultInfo().then(v => setVaultInfo(v)).catch(() => {})
    }
  }, [])

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
      if (isNative()) {
        const input = document.createElement('input')
        input.type = 'file'
        input.accept = 'image/*'
        input.capture = 'environment'
        input.onchange = () => {
          const files = input.files
          if (files && files.length > 0) {
            const f = files[0]
            setMediaFiles(prev => [...prev, f])
            if (!modalities.includes('screenshot')) setModalities([...modalities, 'screenshot'])
          }
        }
        input.click()
        return
      }
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
      const now = new Date()
      const d = now.toISOString().slice(0,10)

      if (isNative()) {
        const vaultInfo = await getVaultInfo()
        if (!vaultInfo) {
          setPopup({ type: 'error', message: 'Please pick a notes directory first.' })
          setSaving(false)
          return
        }
        const clipText = modalities.includes('clipboard')
          ? await (async () => {
              try {
                const resp = await navigator.clipboard.readText()
                return resp || ''
              } catch {
                return ''
              }
            })()
          : ''
        const capture = {
          timestamp: now,
          content,
          clipboard: clipText,
          context,
          tags,
          sources,
          modalities,
          created_date: d,
          last_edited_date: d,
          media_files: mediaFiles.map(f => ({ path: `${vaultInfo.mediaDirAbs}/${f.name}`, type: (f as any).type || 'file', name: f.name }))
        }
        const { filename, content: md } = formatCaptureMarkdown(capture as any, `${vaultInfo.captureDirAbs}`)
        const mediaItems = await Promise.all(mediaFiles.map(f => new Promise<{ name: string; type?: string; dataBase64: string }>((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = () => {
            const res = reader.result as string
            const base64 = res.split(',')[1] || ''
            resolve({ name: f.name, type: (f as any).type || undefined, dataBase64: base64 })
          }
          reader.onerror = () => reject(reader.error)
          reader.readAsDataURL(f)
        })))
        const res = await nativeSave({ filename, content: md, media: mediaItems })
        if (res.ok) {
          setSaveSuccess(true)
          setTimeout(() => setSaveSuccess(false), 2000)
          resetForm()
        } else {
          setPopup({ type: 'error', message: 'Save failed on device' })
        }
        return
      }

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
      if (j.verified !== false) {
        setSaveSuccess(true)
        setTimeout(() => setSaveSuccess(false), 2000)
        resetForm()
      } else {
        setPopup({ type: 'error', message: 'Save failed: File verification failed' })
      }
    } catch (error) {
      console.error('Save failed:', error)
      setPopup({ type: 'error', message: `Save failed: ${error instanceof Error ? error.message : 'Unknown error'}` })
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
      <ModalityBar 
        modalities={modalities} 
        onToggle={toggleModality} 
        onScreenshot={onScreenshot}
        useIcons={config?.ui?.use_modality_icons || false}
      />
      <CaptureForm
        content={content} setContent={setContent}
        context={context} setContext={setContext}
        tags={tags} setTags={setTags}
        sources={sources} setSources={setSources}
        onFiles={onFiles}

        saving={saving}
        onSave={handleSave}
      />
      {isNative() && (
        <div style={{ marginBottom: '8px' }}>
          <button onClick={async () => {
            const ok = await pickVaultDirectory()
            if (!ok) {
              setPopup({ type: 'error', message: 'Directory selection canceled or failed' })
            } else {
              const v = await getVaultInfo()
              setVaultInfo(v)
            }
          }}>
            Pick Notes Directory
          </button>
          {vaultInfo && (
            <div style={{ marginTop: '6px', fontSize: '0.9em', color: '#666' }}>
              <div><strong>Capture dir:</strong> {vaultInfo.captureDirAbs}</div>
              <div><strong>Media dir:</strong> {vaultInfo.mediaDirAbs}</div>
            </div>
          )}
        </div>
      )}

      {isNative() && (
        <div style={{ marginBottom: '8px' }}>
          <button onClick={async () => {
            const ok = await pickVaultDirectory()
            if (!ok) setPopup({ type: 'error', message: 'Directory selection canceled or failed' })
          }}>
            Pick Notes Directory
          </button>
        </div>
      )}

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
      {saveSuccess && (
        <div className="save-success">
          <div className="checkmark">✓</div>
        </div>
      )}
      {popup && (
        <div className={`popup ${popup.type}`} onClick={() => setPopup(null)}>
          {popup.message}
        </div>
      )}
    </div>
  )
}

export default App
