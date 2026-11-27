import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import WasteAnalyzer from '../components/WasteAnalyzer'
import RecoveryPathwayGrid from '../components/RecoveryPathwayGrid'
import { streamInventory } from '../api'

vi.mock('../api', () => ({signIn: vi.fn(async () => true), streamInventory: vi.fn()}))

it('keeps completed rows on cancellation and ignores stale snapshots', async () => {
  let publish
  let cancelSignal
  streamInventory.mockImplementation((_body, snapshot, signal) => {
    publish = snapshot
    cancelSignal = signal
    return new Promise(resolve => signal.addEventListener('abort', resolve, {once:true}))
  })
  const onResult = vi.fn()
  render(<WasteAnalyzer onResult={onResult} />)
  fireEvent.change(screen.getByLabelText('Material description'), {target:{value:'felt loom trimmings'}})
  fireEvent.change(screen.getByLabelText('Quantity'), {target:{value:'5'}})
  fireEvent.click(screen.getByRole('button', {name:'Analyze Waste Streams'}))
  await waitFor(() => expect(streamInventory).toHaveBeenCalledTimes(1))
  const snapshot = {items:[], completed_items:1, total_items:1, pathway_count:0, verified_option_count:0}
  publish(snapshot)
  expect(await screen.findByText('1 / 1')).toBeVisible()
  expect(screen.getByText('Recovery pathways')).toBeVisible()
  for (const label of ['Verified partners', 'Public service leads', 'Confirmed net return'])
    expect(screen.queryByText(label)).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', {name:'Cancel analysis'}))
  expect(cancelSignal.aborted).toBe(true)
  publish({...snapshot, completed_items:0})
  expect(screen.getByText('1 / 1')).toBeVisible()
  expect(onResult).toHaveBeenLastCalledWith(snapshot)
})
it('shows reviewed regional services and keeps Maps separate from public evidence', () => {
  const maps = 'https://www.google.com/maps/search/?api=1&query=waste+paper+600042'
  render(<RecoveryPathwayGrid item={{ material: 'Waste paper', intelligence: {
    research_status: 'pending', pathways: [{ category: 'recycle', title: 'Recycle paper',
      maps_search_links: [{ label: 'Immediate locality', url: maps }],
      public_services: [{ organization: 'Scrap Trove', provenance: 'reviewed_reference',
        coverage: 'documented_region', source_url: 'https://scraptrove.com/' }],
    }],
  } }} />)
  fireEvent.click(screen.getByText('Recommended local and remote services'))
  expect(screen.getByText('Scrap Trove')).toBeVisible()
  expect(screen.getByText(/Documented regional service/)).toBeVisible()
  expect(screen.getByRole('link', { name: /view public listing/i })).toHaveAttribute('href', 'https://scraptrove.com/')
  expect(screen.getAllByRole('link').some(link => link.getAttribute('href') === maps)).toBe(true)
})
