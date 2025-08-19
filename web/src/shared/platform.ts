declare global {
  interface Window {
    Capacitor?: any
    KMS?: any
  }
}

type Bridge =
  | { kind: 'capacitor'; api: any }
  | { kind: 'webview'; api: any }

function getBridge(): Bridge | null {
  const w = window as any
  const c = w.Capacitor
  if (c && c.Plugins && c.Plugins.KMS) return { kind: 'capacitor', api: c.Plugins.KMS }
  if (w.KMS) return { kind: 'webview', api: w.KMS }
  return null
}

export function isNative(): boolean {
  const w = window as any
  const c = w.Capacitor
  if (c && (c.isNativePlatform || c.Plugins)) return true
  if (w.KMS) return true
  return false
}

export type NativeMediaItem = {
  name: string
  type?: string
  dataBase64: string
}

type SavePayload = {
  filename: string
  content: string
  media?: NativeMediaItem[]
}

function parseMaybeJson<T = any>(val: any): T | null {
  if (val == null) return null
  if (typeof val === 'object') return val as T
  if (typeof val === 'string') {
    try { return JSON.parse(val) as T } catch { return null }
  }
  return null
}

export async function pickVaultDirectory(): Promise<boolean> {
  const b = getBridge()
  if (!b) return false
  if (b.kind === 'capacitor') {
    const res = await b.api.pickVaultDirectory()
    return !!(res && res.ok)
  } else {
    const raw = await b.api.pickVaultDirectory()
    const res = parseMaybeJson(raw)
    return !!(res && (res as any).ok)
  }
}

export async function getVaultInfo(): Promise<{ captureDirAbs: string; mediaDirAbs: string } | null> {
  const b = getBridge()
  if (!b) return null
  if (b.kind === 'capacitor') {
    const res = await b.api.getVaultInfo()
    if (res && res.captureDirAbs && res.mediaDirAbs) return res
    return null
  } else {
    const raw = await b.api.getVaultInfo()
    const res = parseMaybeJson<{ captureDirAbs: string; mediaDirAbs: string }>(raw)
    if (res && res.captureDirAbs && res.mediaDirAbs) return res
    return null
  }
}

export async function nativeSave(payload: SavePayload): Promise<{ ok: boolean }> {
  const b = getBridge()
  if (!b) return { ok: false }
  if (b.kind === 'capacitor') {
    const res = await b.api.saveMarkdownAndMedia(payload)
    return { ok: !!(res && res.ok) }
  } else {
    const raw = await b.api.saveMarkdownAndMedia(JSON.stringify(payload))
    const res = parseMaybeJson(raw)
    return { ok: !!(res && (res as any).ok) }
  }
}
