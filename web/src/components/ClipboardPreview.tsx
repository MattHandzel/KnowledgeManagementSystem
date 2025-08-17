import React, { useEffect, useState } from 'react'

const ClipboardPreview: React.FC<{ intervalMs: number }> = ({ intervalMs }) => {
  const [text, setText] = useState<string>('')

  useEffect(() => {
    let mounted = true
    let t: any
    const read = async () => {
      try {
        const response = await fetch('/api/clipboard')
        const data = await response.json()
        if (mounted) setText(data.content || '')
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

  const firstLine = (text || '').split('\n')[0] || ''
  return (
    <div className="clipboard">
      <div className="title">Clipboard Preview</div>
      <div className="body">
        {text ? <div>{firstLine.length > 160 ? firstLine.slice(0,157)+'...' : firstLine}</div> : <div>(clipboard empty)</div>}
      </div>
    </div>
  )
}

export default ClipboardPreview
