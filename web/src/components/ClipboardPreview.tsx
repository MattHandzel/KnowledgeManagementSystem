import React, { useEffect, useState } from 'react'

const ClipboardPreview: React.FC<{ intervalMs: number }> = ({ intervalMs }) => {
  const [text, setText] = useState<string>('')

  useEffect(() => {
    let mounted = true
    let t: any
    const read = async () => {
      try {
        const s = await navigator.clipboard.readText()
        if (mounted) setText(s || '')
      } catch {
        if (mounted) setText('')
      }
    }
    const loop = () => {
      read().finally(() => { t = setTimeout(loop, intervalMs) })
    }
    loop()
    return () => { mounted = false; if (t) clearTimeout(t) }
  }, [intervalMs])

  const lines = (text || '').split('\n')
  return (
    <div className="clipboard">
      <div className="title">Clipboard Preview</div>
      <div className="body">
        {text ? lines.map((l, i) => <div key={i}>{l.length > 160 ? l.slice(0,157)+'...' : l}</div>) : <div>(clipboard empty)</div>}
      </div>
    </div>
  )
}

export default ClipboardPreview
