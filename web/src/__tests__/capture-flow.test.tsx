import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from '../App'

global.fetch = vi.fn().mockImplementation((url: string, init?: any) => {
  if (url === '/api/config') {
    return Promise.resolve({ json: () => Promise.resolve({ vault: { path: '', capture_dir: '', media_dir: '' }, ui: { clipboard_poll_ms: 200 }, is_dev: true }) })
  }
  if (url === '/api/clipboard') {
    return Promise.resolve({ json: () => Promise.resolve({ content: 'clip', type: 'text' }) })
  }
  if (url === '/api/screenshot') {
    return Promise.resolve({ json: () => Promise.resolve({ success: true, path: '/tmp/s1.png' }) })
  }
  if (url === '/api/capture') {
    return Promise.resolve({ json: () => Promise.resolve({ verified: true, saved_to: '/tmp/x.md' }) })
  }
  return Promise.resolve({ json: () => Promise.resolve({}) })
}) as any

describe('capture flow', () => {
  beforeEach(() => {
    (global.fetch as any).mockClear()
  })

  it('saves via Ctrl+Enter hotkey', async () => {
    render(<App />)
    fireEvent.keyDown(window, { key: 'Enter', ctrlKey: true })
    await waitFor(() => {
      expect((global.fetch as any)).toHaveBeenCalledWith('/api/capture', expect.anything())
    })
  })

})
