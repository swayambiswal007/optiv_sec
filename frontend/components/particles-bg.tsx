"use client"

import { useEffect, useRef } from "react"

type Dot = { x: number; y: number; vx: number; vy: number; r: number }

export function ParticlesBg() {
  const ref = useRef<HTMLCanvasElement | null>(null)
  const rafRef = useRef<number | null>(null)

  useEffect(() => {
    const canvas = ref.current!
    const ctx = canvas.getContext("2d")!
    let w = (canvas.width = window.innerWidth)
    let h = (canvas.height = window.innerHeight)

    const onResize = () => {
      w = canvas.width = window.innerWidth
      h = canvas.height = window.innerHeight
    }
    window.addEventListener("resize", onResize)

    const dots: Dot[] = Array.from({ length: 50 }).map(() => ({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      r: 1 + Math.random() * 1.5,
    }))

    const draw = () => {
      ctx.clearRect(0, 0, w, h)
      // subtle dark bg overlay (very low alpha to avoid interfering with UI)
      // dots in cyan-ish and white for subtle sparkle
      dots.forEach((d) => {
        d.x += d.vx
        d.y += d.vy
        if (d.x < 0 || d.x > w) d.vx *= -1
        if (d.y < 0 || d.y > h) d.vy *= -1

        ctx.beginPath()
        ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2)
        // use CSS variable color-primary with a faint alpha for consistency
        ctx.fillStyle = "rgba(6, 182, 212, 0.08)" // matches --color-primary subtly
        ctx.fill()
      })

      rafRef.current = requestAnimationFrame(draw)
    }

    rafRef.current = requestAnimationFrame(draw)
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      window.removeEventListener("resize", onResize)
    }
  }, [])

  return <canvas ref={ref} className="pointer-events-none fixed inset-0 z-0" aria-hidden />
}
