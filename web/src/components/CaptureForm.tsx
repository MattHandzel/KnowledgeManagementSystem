import React from 'react'

type Props = {
  content: string
  setContent: (v: string) => void
  context: string
  setContext: (v: string) => void

  tagsList: string[]
  setTagsList: (fn: (prev: string[]) => string[]) => void
  tagInput: string
  onTagInputChange: (v: string) => void
  onTagBackspace: () => void

  sourcesList: string[]
  setSourcesList: (fn: (prev: string[]) => string[]) => void
  sourceInput: string
  onSourceInputChange: (v: string) => void
  onSourceBackspace: () => void

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
          <div className="chips">
            {p.tagsList.map((t, i) => (
              <span key={`${t}-${i}`} className="chip">
                {t}
                <button aria-label={`remove ${t}`} onClick={() => p.setTagsList(prev => prev.filter((_, idx) => idx !== i))}>×</button>
              </span>
            ))}
            <input
              value={p.tagInput}
              onChange={e => p.onTagInputChange(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Backspace') p.onTagBackspace()
              }}
              placeholder="type then ', '"
            />
          </div>
        </div>
      </div>
      <label>Sources</label>
      <div className="chips">
        {p.sourcesList.map((s, i) => (
          <span key={`${s}-${i}`} className="chip">
            {s}
            <button aria-label={`remove ${s}`} onClick={() => p.setSourcesList(prev => prev.filter((_, idx) => idx !== i))}>×</button>
          </span>
        ))}
        <input
          value={p.sourceInput}
          onChange={e => p.onSourceInputChange(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Backspace') p.onSourceBackspace()
          }}
          placeholder="type then ', '"
        />
      </div>
      <label>Attach files</label>
      <input type="file" onChange={e => p.onFiles(e.target.files)} multiple />
      <div className="actions">
        <button onClick={p.onSave} disabled={p.saving}>{p.saving ? 'Saving...' : 'Save (Ctrl+S)'}</button>
      </div>
    </div>
  )
}

export default CaptureForm
