import { fireEvent, render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import SustainabilityAchievements from '../components/SustainabilityAchievements'
import DigitalTwinCampus from '../components/DigitalTwinCampus'
import ResourceLossHeatmap from '../components/ResourceLossHeatmap'

import InterventionSimulator from '../components/InterventionSimulator'
import ImpactProjection from '../components/ImpactProjection'
import AnalysisErrorBoundary from '../components/AnalysisErrorBoundary'

it('excludes unsupported financial scenarios from a water-only upload', () => {
  render(<InterventionSimulator uploadResult={{analysis_metadata:{anomaly_detection_available:false}}} />)
  expect(screen.getByText('Upgrade Data Resolution')).toBeInTheDocument()
  expect(screen.queryByText(/Waste Segregation Programme|Compost Organic Waste|Install Rooftop Solar/i)).toBeNull()
})

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

  it('uses upload findings without awarding demo achievements', () => {
    render(<SustainabilityAchievements uploadResult={{ water: { anomaly_events: [{}] } }} />)
    expect(screen.getByText('1 flagged resource events in this analysis.')).toBeInTheDocument()
    expect(screen.queryByText(/3 recovery pathways|certified!|achievements unlocked/i)).toBeNull()
  })

  it('renders in upload mode without crashing', () => {
    const uploadResult = { org_name: 'Test Org', org_type: 'University' }
    expect(() =>
      render(<SustainabilityAchievements uploadResult={uploadResult} />)
    ).not.toThrow()
  })
})


it('shows uploaded logical zones and retains the same meter evidence in the Loss Map', () => {
  const water = {status: 'analyzed', total_consumption_liters: 105, resource_profile: {
    by_zone: [{zone: 'North Annex', amount: 105}],
  }, anomaly_events: [{location: 'North Annex', estimated_waste_liters: 12, meter_id: 'fixture-meter',
    timestamp: '2026-11-05T18:30:00+00:00', evidence_status: 'abnormal_consumption'}]}
  const result = {water, analysis_metadata: {anomaly_detection_available: true}}
  render(<><DigitalTwinCampus uploadResult={result} />
    <ResourceLossHeatmap uploadResult={result} waterData={water} /></>)
  expect(screen.getAllByText('North Annex').length).toBeGreaterThan(0)
  expect(screen.getAllByText('105 L').length).toBeGreaterThan(0)
  expect(screen.getByText(/Meter fixture-meter/)).toBeInTheDocument()
  expect(screen.queryByAltText('Illustrative demonstration campus')).not.toBeInTheDocument()
})


it('renders demo projections when Analyze returns both simulated resources', () => {
  render(<ImpactProjection waterData={{total_wasted_liters: 420}} energyData={{total_wasted_kwh: 18}} />)
  expect(screen.getByRole('heading', {name: '30-Day Impact Projection'})).toBeVisible()
  expect(screen.getByText(/7-day simulation window/)).toBeVisible()
})


it('keeps navigation visible and retries a failed results render', () => {
  let fail = true
  function Results() {
    if (fail) throw new Error('Fixture render failure')
    return <h2>Analysis results</h2>
  }

  render(<><nav>New Analysis</nav><AnalysisErrorBoundary analysis><Results /></AnalysisErrorBoundary></>,
    {onCaughtError: () => {}})
  expect(screen.getByText('New Analysis')).toBeVisible()
  expect(screen.getByRole('alert')).toBeVisible()
  fail = false
  fireEvent.click(screen.getByRole('button', {name: 'Retry displaying results'}))
  expect(screen.getByRole('heading', {name: 'Analysis results'})).toBeVisible()
})

it.each([
  [{total_consumption_liters: 20}, undefined, 'water', /20 L/],
  [undefined, {total_consumption_kwh: 12}, 'energy', /12 kWh/],
])('renders available resource projections when the other resource is absent', (water, energy, label, amount) => {
  render(<ImpactProjection uploadResult={{}} waterData={water} energyData={energy} />)
  expect(screen.getByRole('heading', {name: label})).toBeVisible()
  expect(screen.getByText(amount)).toBeVisible()
})
