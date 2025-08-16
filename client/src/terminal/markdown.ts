export type CaptureData = {
  content: string
  context: string
  tags: string[]
  sources: string[]
  modalities: string[]
  timestamp: string
  capture_id: string
  metadata?: Record<string, unknown>
}

function pad(n: number) {
  return n.toString().padStart(2, "0")
}

export function generateCaptureId(date = new Date()) {
  const yyyy = date.getFullYear()
  const MM = pad(date.getMonth() + 1)
  const dd = pad(date.getDate())
  const hh = pad(date.getHours())
  const mm = pad(date.getMinutes())
  const ss = pad(date.getSeconds())
  const ms = date.getMilliseconds().toString().padStart(3, "0")
  return `${yyyy}${MM}${dd}_${hh}${mm}${ss}_${ms}`
}

export function toMarkdown(data: CaptureData) {
  const yamlLines: string[] = [
    "---",
    `timestamp: "${data.timestamp}"`,
    `capture_id: "${data.capture_id}"`,
    `modalities: [${data.modalities.map((m) => `"${m}"`).join(", ")}]`,
    `context: ${data.context.trim() ? `{ note: "${escapeYaml(data.context)}" }` : "null"}`,
    `sources: [${data.sources.map((s) => `"${escapeYaml(s)}"`).join(", ")}]`,
    `tags: [${data.tags.map((t) => `"${escapeYaml(t)}"`).join(", ")}]`,
    `processing_status: "raw"`,
    `importance: 0.5`,
    `metadata: {}`,
    "---",
    ""
  ]

  const sections: string[] = []
  if (data.content.trim()) {
    sections.push("## Content\n\n" + data.content.trim() + "\n")
  }
  if (data.modalities.includes("clipboard")) {
    sections.push("## Clipboard\n\n")
  }
  if (data.modalities.some((m) => m === "screenshot" || m === "audio" || m === "files")) {
    sections.push("## Media\n\n")
  }

  return yamlLines.join("\n") + sections.join("\n")
}

function escapeYaml(s: string) {
  return s.replace(/\\/g, "\\\\").replace(/"/g, '\\"')
}

export function downloadMarkdown(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
