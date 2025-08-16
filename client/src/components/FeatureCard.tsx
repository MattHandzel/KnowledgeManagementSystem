import React from "react"

type Props = {
  title: string
  description: string
  icon?: React.ReactNode
}

export default function FeatureCard({ title, description, icon }: Props) {
  return (
    <div className="rounded-xl border border-neutral-200 p-6 hover:shadow-sm transition-shadow bg-white">
      <div className="mb-3 text-brand-600">{icon}</div>
      <h3 className="text-lg font-semibold mb-1">{title}</h3>
      <p className="text-neutral-600 text-sm leading-6">{description}</p>
    </div>
  )
}
