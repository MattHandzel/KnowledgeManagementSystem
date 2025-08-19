export {}

const shouldPrefix = () =>
  typeof location !== 'undefined' && location.protocol === 'file:'

const base =
  (typeof window !== 'undefined' && (window as any).__KMS_API_BASE) ||
  (shouldPrefix() ? 'http://127.0.0.1:14321' : '')

const origFetch: typeof fetch = globalThis.fetch.bind(globalThis)

globalThis.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
  let url: string
  if (typeof input === 'string') url = input
  else if (input instanceof URL) url = input.toString()
  else url = input.url

  if (url.startsWith('/api')) {
    const full = base + url
    if (typeof input === 'string' || input instanceof URL) {
      return origFetch(full, init)
    } else {
      const req = new Request(full, input)
      return origFetch(req, init)
    }
  }
  return origFetch(input as any, init)
}
