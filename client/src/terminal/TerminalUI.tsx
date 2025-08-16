import React, { useEffect, useMemo, useRef, useState } from "react"
import { interpretKey, Field, UIMode } from "./keybindings"
import { downloadMarkdown, generateCaptureId, toMarkdown } from "./markdown"

const ALL_MODALITIES = ["text", "clipboard", "screenshot", "audio", "files"]

type Idea = {
  capture_id: string
  title: string
  content: string
  timestamp: string
  modalities: string[]
  tags: string[]
  sources: string[]
  context: string
}

export default function TerminalUI() {
  const [mode, setMode] = useState<UIMode>("insert")
  const [activeField, setActiveField] = useState<Field>("content")
  const [showHelp, setShowHelp] = useState(false)
  const [content, setContent] = useState("")
  const [context, setContext] = useState("")
  const [tags, setTags] = useState("")
  const [sources, setSources] = useState("")
  const [activeModalities, setActiveModalities] = useState<string[]>(["text"])
  const [ideas, setIdeas] = useState<Idea[]>([])
  const [browseIndex, setBrowseIndex] = useState(0)
  const contentRef = useRef<HTMLTextAreaElement>(null)
  const contextRef = useRef<HTMLInputElement>(null)
  const tagsRef = useRef<HTMLInputElement>(null)
  const sourcesRef = useRef<HTMLInputElement>(null)

  const fieldOrder: Field[] = ["content", "context", "tags", "sources", "modalities"]

  function focusActive() {
    if (activeField === "content") contentRef.current?.focus()
    if (activeField === "context") contextRef.current?.focus()
    if (activeField === "tags") tagsRef.current?.focus()
    if (activeField === "sources") sourcesRef.current?.focus()
  }

  useEffect(() => {
    focusActive()
  }, [activeField, mode])

  useEffect(() => {
    function handler(e: KeyboardEvent) {
      const action = interpretKey(e)
      if (action === "noop") return

      if (typeof action === "string") {
        if (
          [
            "save",
            "cancel",
            "help",
            "next_field",
            "prev_field",
            "toggle_browse",
            "toggle_edit",
            "toggle_modality_space",
            "browse_up",
            "browse_down"
          ].includes(action)
        ) {
          e.preventDefault()
        }
      } else {
        e.preventDefault()
      }

      if (action === "save") {
        const capture_id = generateCaptureId()
        const timestamp = new Date().toISOString()
        const payload = {
          content,
          context,
          tags: splitCsv(tags),
          sources: splitCsv(sources),
          modalities: [...activeModalities],
          timestamp,
          capture_id
        }
        const md = toMarkdown(payload)
        downloadMarkdown(`${capture_id}.md`, md)
        const title = content.split("\n").find((l) => l.trim().length) ?? "(untitled)"
        setIdeas((prev) => [{ capture_id, title: title.slice(0, 80), content, timestamp, modalities: payload.modalities, tags: payload.tags, sources: payload.sources, context }, ...prev])
      } else if (action === "cancel") {
        setContent("")
        setContext("")
        setTags("")
        setSources("")
        setActiveModalities(["text"])
        setMode("insert")
        setActiveField("content")
      } else if (action === "help") {
        setShowHelp((v) => !v)
      } else if (action === "next_field") {
        const idx = fieldOrder.indexOf(activeField)
        const next = fieldOrder[(idx + 1) % fieldOrder.length]
        setActiveField(next)
      } else if (action === "prev_field") {
        const idx = fieldOrder.indexOf(activeField)
        const prev = fieldOrder[(idx - 1 + fieldOrder.length) % fieldOrder.length]
        setActiveField(prev)
      } else if (action === "toggle_browse") {
        if (mode === "browse") {
          setMode("insert")
          setActiveField("content")
        } else {
          setMode("browse")
          setActiveField("idea_list")
          setBrowseIndex(0)
        }
      } else if (action === "toggle_edit") {
        if (mode === "browse" && ideas[browseIndex]) {
          const idea = ideas[browseIndex]
          setContent(idea.content)
          setContext(idea.context)
          setTags(idea.tags.join(", "))
          setSources(idea.sources.join(", "))
          setActiveModalities(idea.modalities)
          setMode("insert")
          setActiveField("content")
        }
      } else if (action === "toggle_modality_space") {
        if (activeField === "modalities") {
          toggleModalityByIndex(0)
        }
      } else if (action === "browse_down" && mode === "browse") {
        setBrowseIndex((i) => Math.min(i + 1, Math.max(ideas.length - 1, 0)))
      } else if (action === "browse_up" && mode === "browse") {
        setBrowseIndex((i) => Math.max(i - 1, 0))
      } else if (typeof action === "object" && action.type === "toggle_modality_number") {
        toggleModalityByIndex(action.index)
      }
    }

    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [content, context, tags, sources, activeModalities, mode, activeField, ideas, browseIndex])

  function toggleModalityByIndex(index: number) {
    const mod = ALL_MODALITIES[index]
    if (!mod) return
    setActiveModalities((prev) => (prev.includes(mod) ? prev.filter((m) => m !== mod) : [...prev, mod]))
  }

  function splitCsv(s: string) {
    return s
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean)
  }

  const helpLines = useMemo(
    () => [
      "Ctrl+S Save • ESC Cancel • Tab/Shift+Tab Switch Field • F1 Help • Ctrl+B Browse • Ctrl+E Edit",
      "Numbers 1-5 toggle modalities: 1=text 2=clipboard 3=screenshot 4=audio 5=files"
    ],
    []
  )

  return (
    <div className="min-h-screen bg-black text-green-200 font-mono">
      <div className="max-w-5xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="text-green-400">Terminal Capture</div>
          <div className="text-xs text-green-500">{mode.toUpperCase()} {showHelp ? "• HELP" : ""}</div>
        </div>

        <div className="mt-2 text-xs text-green-600">{helpLines[0]}</div>
        <div className="text-xs text-green-600">{helpLines[1]}</div>

        <div className="mt-4 grid grid-cols-1 gap-2">
          <FieldBox title="Content" active={activeField === "content"}>
            <textarea
              ref={contentRef}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={10}
              className="w-full bg-black text-green-100 outline-none resize-none"
              placeholder="Type your idea..."
            />
          </FieldBox>

          <FieldRow>
            <FieldBox title="Context" active={activeField === "context"}>
              <input
                ref={contextRef}
                value={context}
                onChange={(e) => setContext(e.target.value)}
                className="w-full bg-black text-green-100 outline-none"
                placeholder="e.g., activity, location…"
              />
            </FieldBox>
            <FieldBox title="Tags" active={activeField === "tags"}>
              <input
                ref={tagsRef}
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="w-full bg-black text-green-100 outline-none"
                placeholder="comma,separated,tags"
              />
            </FieldBox>
          </FieldRow>

          <FieldRow>
            <FieldBox title="Sources" active={activeField === "sources"}>
              <input
                ref={sourcesRef}
                value={sources}
                onChange={(e) => setSources(e.target.value)}
                className="w-full bg-black text-green-100 outline-none"
                placeholder="comma,separated,sources"
              />
            </FieldBox>
            <FieldBox title="Modalities" active={activeField === "modalities"}>
              <div className="flex flex-wrap gap-2">
                {ALL_MODALITIES.map((m, idx) => {
                  const active = activeModalities.includes(m)
                  return (
                    <button
                      key={m}
                      type="button"
                      onClick={() => toggleModalityByIndex(idx)}
                      className={`px-2 py-1 text-xs border ${active ? "border-green-400 text-black bg-green-400" : "border-green-700 text-green-300 bg-black"}`}
                    >
                      {idx + 1}:{m}
                    </button>
                  )
                })}
              </div>
            </FieldBox>
          </FieldRow>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-2">
          <FieldBox title="Idea List" active={mode === "browse" && activeField === "idea_list"}>
            {ideas.length === 0 ? (
              <div className="text-green-700 text-sm">No ideas captured this session. Save with Ctrl+S.</div>
            ) : (
              <ul className="text-sm max-h-48 overflow-auto">
                {ideas.map((idea, i) => (
                  <li
                    key={idea.capture_id}
                    className={`px-2 py-1 ${i === browseIndex && mode === "browse" ? "bg-green-900 text-green-100" : "text-green-300"}`}
                    onMouseEnter={() => setBrowseIndex(i)}
                  >
                    [{i + 1}] {idea.title}
                  </li>
                ))}
              </ul>
            )}
          </FieldBox>

          <FieldBox title="Preview">
            <pre className="text-xs text-green-300 whitespace-pre-wrap overflow-auto max-h-48">
{toMarkdown({
  content,
  context,
  tags: content ? splitCsv(tags) : [],
  sources: content ? splitCsv(sources) : [],
  modalities: activeModalities,
  timestamp: new Date().toISOString(),
  capture_id: "preview"
})}
            </pre>
          </FieldBox>
        </div>

        {showHelp && (
          <div className="fixed inset-0 bg-black/90 flex items-center justify-center">
            <div className="max-w-2xl w-full border border-green-700 p-4">
              <div className="text-green-400 mb-2">Help</div>
              <ul className="text-green-300 text-sm space-y-1">
                <li>Ctrl+S Save capture and download as .md</li>
                <li>ESC Clear all fields</li>
                <li>Tab / Shift+Tab Switch field</li>
                <li>F1 Toggle help</li>
                <li>Ctrl+B Toggle browse mode</li>
                <li>Ctrl+E Load selected idea into editor</li>
                <li>Numbers 1-5 Toggle modalities</li>
              </ul>
              <div className="text-green-600 text-xs mt-3">Press F1 to close</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function FieldBox({ title, active, children }: { title: string; active?: boolean; children: React.ReactNode }) {
  return (
    <div className={`border ${active ? "border-green-400" : "border-green-800"} p-2`}>
      <div className={`text-xs mb-1 ${active ? "text-green-400" : "text-green-600"}`}>{title}</div>
      {children}
    </div>
  )
}

function FieldRow({ children }: { children: React.ReactNode }) {
  return <div className="grid grid-cols-1 md:grid-cols-2 gap-2">{children}</div>
}
