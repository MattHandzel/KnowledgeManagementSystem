declare global {
  interface Window {
    Capacitor?: any
    KMS?: any
  }
}

function getKMS(): any | null {
  const c = (window as any).Capacitor
  if (c && c.Plugins && c.Plugins.KMS) return c.Plugins.KMS
  if ((window as any).KMS) return (window as any).KMS
  return null
}

export function isNative(): boolean {
  const c = (window as any).Capacitor
  if (c && (c.isNativePlatform || c.Plugins)) return true
  if ((window as any).KMS) return true
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

export async function pickVaultDirectory(): Promise<boolean> {
  const kms = getKMS()
  if (!kms) return false
  const res = await kms.pickVaultDirectory()
  return !!res?.ok
}

export async function getVaultInfo(): Promise<{ captureDirAbs: string; mediaDirAbs: string } | null> {
  const kms = getKMS()
  if (!kms) return null
  const res = await kms.getVaultInfo()
  if (res && res.captureDirAbs && res.mediaDirAbs) return res
  return null
}

export async function nativeSave(payload: SavePayload): Promise<{ ok: boolean }> {
  const kms = getKMS()
  if (!kms) return { ok: false }
  const res = await kms.saveMarkdownAndMedia(payload)
  return { ok: !!res?.ok }
}
