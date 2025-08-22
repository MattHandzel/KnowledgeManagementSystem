import yaml from 'js-yaml'

type CaptureInput = {
  timestamp?: Date
  capture_id?: string
  content?: string
  clipboard?: string
  context?: string | Record<string, string>
  tags?: string[] | string
  sources?: string[] | string
  modalities?: string[]
  location?: any
  metadata?: Record<string, unknown>
  created_date?: string
  last_edited_date?: string
  media_files?: { path: string; type?: string; name?: string }[]
}

function generateCaptureId(ts: Date): string {
  const d = new Date(ts)
  const iso = d.toISOString()
  return iso
}

function normalizeArray(v: unknown): string[] {
  if (Array.isArray(v)) return v as string[]
  if (typeof v === 'string') {
    return v.split(',').map(s => s.trim()).filter(Boolean)
  }
  return []
}

function getContextEntities(v: unknown): string[] {
  if (!v) return []
  if (typeof v === 'string') return v ? [v] : []
  if (typeof v === 'object' && v !== null) {
    return Object.values(v as Record<string, string>).filter(Boolean)
  }
  return []
}

function relativeMediaPath(mediaPath: string, captureDir: string): string {
  try {
    const from = captureDir.endsWith('/') ? captureDir : captureDir + '/'
    if (mediaPath.startsWith(from)) return mediaPath.slice(from.length)
    return mediaPath
  } catch {
    return mediaPath
  }
}

export function formatCaptureMarkdown(capture: CaptureInput, vaultCaptureDirAbs: string): { filename: string; content: string } {
  const ts = capture.timestamp ? new Date(capture.timestamp) : new Date()
  const captureId = capture.capture_id || generateCaptureId(ts)
  const isoTs = capture.timestamp ? (capture.timestamp as Date).toISOString() : ts.toISOString()
  const created = capture.created_date || ts.toISOString().slice(0, 10)
  const edited = capture.last_edited_date || ts.toISOString().slice(0, 10)
  const modalities = capture.modalities && capture.modalities.length ? capture.modalities : ['text']
  const fm: any = {
    timestamp: isoTs,
    id: captureId,
    aliases: [captureId],
    capture_id: captureId,
    modalities,
    context: getContextEntities(capture.context),
    sources: normalizeArray(capture.sources),
    tags: normalizeArray(capture.tags),
    location: capture.location,
    metadata: capture.metadata || {},
    processing_status: 'raw',
    created_date: created,
    last_edited_date: edited,
    importance: null
  }
  const sections: string[] = []
  const mainContent = (capture.content || '').toString()
  if (mainContent.trim()) {
    sections.push(`## Content\n${mainContent}\n`)
  }
  const clip = (capture.clipboard || '').toString()
  if (clip.trim()) {
    if (clip.startsWith('```') || clip.includes('\n')) {
      sections.push(`## Clipboard\n${clip}\n`)
    } else {
      sections.push(`## Clipboard\n\`\`\`\n${clip}\n\`\`\`\n`)
    }
  }
  const media = capture.media_files || []
  if (media.length) {
    for (const m of media) {
      const t = m.type || 'file'
      const p = m.path || ''
      if (t === 'screenshot') {
        sections.push(`## Screenshot\n${p}\n`)
      } else if (t === 'audio') {
        const rel = relativeMediaPath(p, vaultCaptureDirAbs)
        sections.push(`## Audio\n[Audio Recording](${rel})\n`)
      } else if (t === 'image') {
        const rel = relativeMediaPath(p, vaultCaptureDirAbs)
        sections.push(`## Image\n![Image](${rel})\n`)
      } else {
        const rel = relativeMediaPath(p, vaultCaptureDirAbs)
        sections.push(`## File\n[Attachment](${rel})\n`)
      }
    }
  }
  const yamlStr = yaml.dump(fm, { flowLevel: -1, sortKeys: false })
  const md = `---\n${yamlStr}---\n${sections.join('')}`
  const filename = `${captureId}.md`
  return { filename, content: md }
}
