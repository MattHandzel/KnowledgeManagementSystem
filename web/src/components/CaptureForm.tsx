import React from 'react'

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
  return (
    <div className="form">
      <label>Content</label>
      <textarea value={p.content} onChange={e => p.setContent(e.target.value)} rows={10} />
      <div className="row">
        <div className="col">
          <label>Context</label>
          <input value={p.context} onChange={e => p.setContext(e.target.value)} placeholder="key: value, or YAML" />
        </div>
        <div className="col">
          <label>Tags</label>
          <input value={p.tags} onChange={e => p.setTags(e.target.value)} placeholder="comma,separated,tags" />
        </div>
      </div>
      <label>Sources</label>
      <input value={p.sources} onChange={e => p.setSources(e.target.value)} placeholder="book: X, website: Y" />
      <div className="actions">
        <button onClick={p.onSave} disabled={p.saving}>{p.saving ? 'Saving...' : 'Save (Ctrl+S)'}</button>
      </div>
    </div>
  )
}

export default CaptureForm
