export type UIMode = "insert" | "normal" | "browse"

export type Field = "content" | "context" | "tags" | "sources" | "modalities" | "idea_list"

export type KeyAction =
  | "save"
  | "cancel"
  | "help"
  | "next_field"
  | "prev_field"
  | "toggle_browse"
  | "toggle_edit"
  | "toggle_modality_space"
  | "browse_up"
  | "browse_down"
  | "noop"

export type ModalityNumberAction = { type: "toggle_modality_number"; index: number }

export function interpretKey(e: KeyboardEvent): KeyAction | ModalityNumberAction {
  if (e.ctrlKey && e.key.toLowerCase() === "s") return "save"
  if (e.key === "Escape") return "cancel"
  if (e.key === "F1") return "help"
  if (e.key === "Tab" && !e.shiftKey) return "next_field"
  if (e.key === "Tab" && e.shiftKey) return "prev_field"
  if (e.ctrlKey && e.key.toLowerCase() === "b") return "toggle_browse"
  if (e.ctrlKey && e.key.toLowerCase() === "e") return "toggle_edit"
  if (e.key === " ") return "toggle_modality_space"
  if (e.key === "j") return "browse_down"
  if (e.key === "k") return "browse_up"
  if (/^[1-9]$/.test(e.key)) return { type: "toggle_modality_number", index: parseInt(e.key, 10) - 1 }
  return "noop"
}
