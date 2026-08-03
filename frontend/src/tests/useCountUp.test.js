import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import useCountUp from '../hooks/useCountUp'

describe('useCountUp', () => {
  beforeEach(() => { vi.useFakeTimers() })
  afterEach(() => { vi.useRealTimers() })

  it('starts at 0', () => {
    const { result } = renderHook(() => useCountUp(100))
    expect(result.current).toBe(0)
  })

  it('returns 0 when target is 0', () => {
    const { result } = renderHook(() => useCountUp(0))
    act(() => { vi.runAllTimers() })
    expect(result.current).toBe(0)
  })

  it('reaches target after animation completes', () => {
    const { result } = renderHook(() => useCountUp(200, 100))
    act(() => { vi.runAllTimers() })
    expect(result.current).toBe(200)
  })

  it('cleans up interval on unmount', () => {
    const { unmount } = renderHook(() => useCountUp(500))
    expect(() => unmount()).not.toThrow()
  })
})
