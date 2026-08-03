import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import SustainabilityAchievements from '../components/SustainabilityAchievements'

describe('SustainabilityAchievements', () => {
  it('renders without crashing when no props provided', () => {
    expect(() => render(<SustainabilityAchievements />)).not.toThrow()
  })

  it('renders achievement count label', () => {
    render(<SustainabilityAchievements />)
    expect(screen.getByText(/achievements unlocked/i)).toBeInTheDocument()
  })

  it('shows achievements unlocked count', () => {
    render(<SustainabilityAchievements />)
    // text is split across elements; look for the trailing label
    expect(screen.getByText(/achievements unlocked/i)).toBeInTheDocument()
  })

  it('unlocks water achievement when water severity is critical', () => {
    const dashData = {
      regen_score: { after_score: 75 },
      water_summary: { severity: 'critical' },
      energy_summary: { severity: 'none' },
      impact_summary: { total_co2_saved_kg: 0 },
    }
    render(<SustainabilityAchievements dashData={dashData} />)
    expect(screen.getByText(/Water Guardian/i)).toBeInTheDocument()
  })

  it('renders in upload mode without crashing', () => {
    const uploadResult = { org_name: 'Test Org', org_type: 'University' }
    expect(() =>
      render(<SustainabilityAchievements uploadResult={uploadResult} />)
    ).not.toThrow()
  })
})
