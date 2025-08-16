import React from "react"
import FeatureCard from "./components/FeatureCard"

function Section({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <section className="max-w-6xl mx-auto px-6 py-12">
      <h2 className="text-2xl md:text-3xl font-semibold mb-6">{title}</h2>
      {children}
    </section>
  )
}

export default function App() {
  const features = [
    {
      title: "Instant",
      description: "Background daemon over Unix sockets for sub-100ms response."
    },
    {
      title: "Terminal UI",
      description: "ncurses interface with semantic, vim-inspired keybindings."
    },
    {
      title: "Multimodal",
      description: "Capture text, clipboard, screenshots, audio, and files."
    },
    {
      title: "Safe by Design",
      description: "Atomic writes, unique IDs, and backups. Plain markdown with YAML."
    },
    {
      title: "Obsidian-friendly",
      description: "Pure markdown stored under your vault for seamless integration."
    },
    {
      title: "NixOS + Hyprland",
      description: "Flake-based dev and Hyprland keybindings for tight integration."
    }
  ]

  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="border-b border-neutral-200 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-md bg-brand-600" />
            <span className="font-semibold">Terminal Capture Daemon</span>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm">
            <a className="text-neutral-700 hover:text-brand-700" href="https://github.com/MattHandzel/KnowledgeManagementSystem" target="_blank" rel="noreferrer">GitHub</a>
            <a className="text-neutral-700 hover:text-brand-700" href="https://github.com/MattHandzel/KnowledgeManagementSystem/blob/devin/1755292819-terminal-capture-daemon/README.md" target="_blank" rel="noreferrer">README</a>
            <a className="text-neutral-700 hover:text-brand-700" href="https://github.com/MattHandzel/KnowledgeManagementSystem/blob/devin/1755292819-terminal-capture-daemon/DESIGN_SPECIFICATION.md" target="_blank" rel="noreferrer">Design</a>
            <a className="text-neutral-700 hover:text-brand-700" href="../docs/REPO_READTHROUGH.md" rel="noreferrer">Repo Read-through</a>
          </nav>
        </div>
      </header>

      <main>
        <section className="max-w-6xl mx-auto px-6 py-16">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-3xl md:text-5xl font-semibold leading-tight mb-4">
                Capture ideas at the speed of thought
              </h1>
              <p className="text-neutral-700 text-lg leading-7 mb-8">
                A lightweight, keyboard-first knowledge capture daemon for NixOS + Hyprland.
                Instant popups. Semantic keybindings. Safe, reversible storage as individual markdown files.
              </p>
              <div className="flex flex-col sm:flex-row gap-3">
                <a
                  href="https://github.com/MattHandzel/KnowledgeManagementSystem"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center justify-center rounded-md bg-brand-600 text-white px-5 py-3 text-sm font-medium hover:bg-brand-700"
                >
                  View on GitHub
                </a>
                <a
                  href="https://github.com/MattHandzel/KnowledgeManagementSystem/blob/devin/1755292819-terminal-capture-daemon/README.md"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center justify-center rounded-md border border-neutral-300 bg-white text-neutral-800 px-5 py-3 text-sm font-medium hover:bg-neutral-50"
                >
                  Quick Start
                </a>
              </div>
            </div>
            <div className="rounded-xl border border-neutral-200 bg-white p-6">
              <div className="text-sm text-neutral-700 mb-3">Flow</div>
              <div className="grid grid-cols-1 gap-3 text-sm">
                <div className="flex items-center gap-3">
                  <div className="h-2 w-2 rounded-full bg-brand-600" />
                  <div>Hyprland keybind</div>
                </div>
                <div className="ml-4 border-l pl-4">
                  <div>→ trigger_capture.py</div>
                  <div className="text-neutral-500">Unix socket</div>
                </div>
                <div className="ml-8 border-l pl-4">
                  <div>→ capture_daemon.py</div>
                  <div className="text-neutral-500">ncurses UI + keybindings</div>
                </div>
                <div className="ml-12 border-l pl-4">
                  <div>→ SafeMarkdownWriter</div>
                  <div className="text-neutral-500">YAML + markdown + media</div>
                </div>
                <div className="ml-16 border-l pl-4">
                  <div>→ ~/notes/capture/raw_capture</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <Section title="Features">
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <FeatureCard key={f.title} title={f.title} description={f.description} />
            ))}
          </div>
        </Section>

        <Section title="How it works">
          <div className="grid md:grid-cols-2 gap-8">
            <div className="rounded-xl border border-neutral-200 bg-white p-6">
              <h3 className="font-semibold mb-2">Keybindings</h3>
              <ul className="text-neutral-700 text-sm leading-7 list-disc pl-5">
                <li>Ctrl+S save</li>
                <li>ESC cancel</li>
                <li>Tab/Shift+Tab navigate fields</li>
                <li>F1 help</li>
                <li>Arrows or h/j/k/l for movement</li>
              </ul>
            </div>
            <div className="rounded-xl border border-neutral-200 bg-white p-6">
              <h3 className="font-semibold mb-2">Modalities</h3>
              <ul className="text-neutral-700 text-sm leading-7 list-disc pl-5">
                <li>Text input</li>
                <li>Clipboard capture</li>
                <li>Screenshots</li>
                <li>Audio recording</li>
                <li>Files and media</li>
              </ul>
            </div>
          </div>
        </Section>

        <Section title="Documentation">
          <div className="flex flex-col sm:flex-row gap-3">
            <a
              className="inline-flex items-center justify-center rounded-md border border-neutral-300 bg-white text-neutral-800 px-5 py-3 text-sm font-medium hover:bg-neutral-50"
              href="https://github.com/MattHandzel/KnowledgeManagementSystem/blob/devin/1755292819-terminal-capture-daemon/DESIGN_SPECIFICATION.md"
              target="_blank"
              rel="noreferrer"
            >
              Design Specification
            </a>
            <a
              className="inline-flex items-center justify-center rounded-md border border-neutral-300 bg-white text-neutral-800 px-5 py-3 text-sm font-medium hover:bg-neutral-50"
              href="https://github.com/MattHandzel/KnowledgeManagementSystem/blob/devin/1755292819-terminal-capture-daemon/README.md"
              target="_blank"
              rel="noreferrer"
            >
              README
            </a>
            <a
              className="inline-flex items-center justify-center rounded-md border border-neutral-300 bg-white text-neutral-800 px-5 py-3 text-sm font-medium hover:bg-neutral-50"
              href="../docs/REPO_READTHROUGH.md"
              rel="noreferrer"
            >
              Repo Read-through
            </a>
          </div>
        </Section>
      </main>

      <footer className="py-10 border-t border-neutral-200 mt-8">
        <div className="max-w-6xl mx-auto px-6 text-sm text-neutral-600">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>© {new Date().getFullYear()} Terminal Capture Daemon</div>
            <div className="flex gap-4">
              <a className="hover:text-neutral-900" href="https://github.com/MattHandzel/KnowledgeManagementSystem" target="_blank" rel="noreferrer">GitHub</a>
              <a className="hover:text-neutral-900" href="../docs/REPO_READTHROUGH.md" rel="noreferrer">Docs</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
