import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'
import App from '../App'

function mockFetchConfigAndCapture() {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input)
    if (url.endsWith('/api/config')) {
      return Promise.resolve(new Response(JSON.stringify({
        vault: { path: '/tmp/vault', capture_dir: 'capture/raw_capture', media_dir: 'capture/raw_capture/media' },
        ui: { clipboard_poll_ms: 100 }
      }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    }
    if (url.endsWith('/api/capture')) {
      return Promise.resolve(new Response(JSON.stringify({
        saved_to: '/tmp/vault/capture/raw_capture/20250101_000000_000.md'
      }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    }
    return Promise.resolve(new Response('{}', { status: 200 }))
  }) as unknown as typeof fetch
  ;(globalThis as any).fetch = fetchMock
  return fetchMock
}

describe('App keybindings and help', () => {
  beforeEach(() => {
    mockFetchConfigAndCapture()
  })

  it('Ctrl+S triggers save and shows toast', async () => {
    render(<App />)
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 's', ctrlKey: true, bubbles: true }))
    const toast = await screen.findByText(/Saved to /i, {}, { timeout: 2000 })
    expect(toast).toBeInTheDocument()
  })

  it('Plain number does not toggle modalities, Ctrl+2 does', async () => {
    const { container } = render(<App />)
    const clipboardBtn = await within(container).findByRole('button', { name: /clipboard/i })
    expect(clipboardBtn).not.toHaveClass('active')
    fireEvent.keyDown(window, { key: '2' })
    expect(clipboardBtn).not.toHaveClass('active')
    fireEvent.keyDown(window, { key: '2', ctrlKey: true })
    await waitFor(() => expect(clipboardBtn).toHaveClass('active'), { timeout: 2000 })
  })

  it('Help overlay toggles via Help button', async () => {
    const { container } = render(<App />)
    const helpBtn = within(container).getByRole('button', { name: /Help/i })
    await userEvent.click(helpBtn)
    const closeBtn = await within(container).findByRole('button', { name: /Close/i })
    expect(closeBtn).toBeInTheDocument()
    await userEvent.click(closeBtn)
    await waitFor(() => expect(within(container).queryByRole('button', { name: /Close/i })).not.toBeInTheDocument())
  })
})
