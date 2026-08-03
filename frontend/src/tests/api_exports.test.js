import { describe, it, expect, vi } from 'vitest'

// Mock axios before importing api.js so no real HTTP calls are made
vi.mock('axios', () => ({
  default: {
    create: () => ({
      get: vi.fn(),
      post: vi.fn(),
    }),
  },
}))

import * as api from '../api.js'

describe('api.js exports', () => {
  it('exports healthCheck as a function', () => {
    expect(typeof api.healthCheck).toBe('function')
  })

  it('exports analyzeWaste as a function', () => {
    expect(typeof api.analyzeWaste).toBe('function')
  })

  it('exports getWasteMaterials as a function', () => {
    expect(typeof api.getWasteMaterials).toBe('function')
  })

  it('exports validateUpload as a function', () => {
    expect(typeof api.validateUpload).toBe('function')
  })

  it('exports analyzeUpload as a function', () => {
    expect(typeof api.analyzeUpload).toBe('function')
  })

  it('exports interpretDatasets as a function', () => {
    expect(typeof api.interpretDatasets).toBe('function')
  })

  it('exports BASE_URL as a string', () => {
    expect(typeof api.BASE_URL).toBe('string')
  })
})
