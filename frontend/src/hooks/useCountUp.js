import { useState, useEffect } from 'react'

export default function useCountUp(target, duration = 1400) {
  const [val, setVal] = useState(0)
  useEffect(() => {
    if (!target) return
    let current = 0
    const step = target / (duration / 16)
    const timer = setInterval(() => {
      current += step
      if (current >= target) { setVal(target); clearInterval(timer) }
      else setVal(Math.floor(current))
    }, 16)
    return () => clearInterval(timer)
  }, [target, duration])
  return val
}
