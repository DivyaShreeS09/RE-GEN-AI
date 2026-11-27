import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import RecoveryMission from '../components/RecoveryMission'
import { clarifyMaterial, createMission, readMission, updateMission, readExecutionJob } from '../api'

vi.mock('../api', () => ({clarifyMaterial: vi.fn(), createMission: vi.fn(), readMission: vi.fn(), updateMission: vi.fn(), readExecutionJob: vi.fn()}))
beforeEach(() => { localStorage.clear(); sessionStorage.clear(); vi.clearAllMocks() })

it('submits only service PIN and facility inputs and displays the actual decision event', async () => {
  const mission = { id: 'fixture', version: 1, state: 'needs_evidence', events: [
    {at: '2026-01-01T00:00:00Z', agent: 'Waste-to-Wealth Agent', action: 'needs_evidence', reason: 'No verified match.'}
  ], result: {options: []} }
  createMission.mockResolvedValue({data: mission})
  readMission.mockResolvedValue({data: mission})
  render(<RecoveryMission />)
  for (const [label, value] of [['Material','paper'],['Condition','dry'],['Quantity (grams)','500'],['Service PIN','600001']])
    fireEvent.change(screen.getByLabelText(label), {target: {value}})
  fireEvent.click(screen.getByRole('button', {name: 'Check reviewed services'}))
  await waitFor(() => expect(screen.getByText(/No verified match/)).toBeVisible())
  expect(createMission.mock.calls[0][0]).toMatchObject({quantity_g: 500, service_pin: '600001', material: 'paper'})
  expect(createMission.mock.calls[0][1]).toBe(false)
  expect(sessionStorage.getItem('regen-mission')).toBe('fixture')
})

it('displays service evidence and declines an offer before reservation', async () => {
  const offered = { id: 'fixture', version: 1, state: 'awaiting_approval', inputs: {}, events: [],
    result: { options: [{service_id:'offer', organization:'Fixture', pathway:'sell', effort:'low',
      transfer:'pickup', reviewed_at:'2026-01-01T00:00:00Z', expires:'2026-02-01T00:00:00Z', net_paise:200}] } }
  sessionStorage.setItem('regen-mission', offered.id)
  readMission.mockResolvedValue({data: offered})
  updateMission.mockResolvedValue({data: {...offered, version:2, state:'needs_evidence', result:{options:[]}}})
  render(<RecoveryMission />)
  expect(await screen.findByText(/low effort/)).toBeVisible()
  fireEvent.click(screen.getByRole('button', {name:'Decline option and replan'}))
  await waitFor(() => expect(updateMission).toHaveBeenCalledWith('fixture', {version:1,action:'reject',service_id:'offer'}, false))
})

it('resumes the same material mission with documented facility clarification', async () => {
  const initial = {id:'unknown',version:1,state:'manual_review',inputs:{condition:'dry',quantity_g:500},
    events:[],result:{options:[],clarification:{question:'Which supplier label identifies the insert?'}}}
  sessionStorage.setItem('regen-mission', initial.id)
  readMission.mockResolvedValue({data:initial})
  clarifyMaterial.mockResolvedValue({data:{...initial,version:2,state:'needs_evidence',
    events:[{at:'2026-01-01T00:00:00Z',agent:'Waste-to-Wealth Agent',reason:'Reviewed insert; no current demand.'}]}})
  render(<RecoveryMission />)
  expect(await screen.findByText('Which supplier label identifies the insert?')).toBeVisible()
  for (const [label,value] of [['Review response','Supplier label checked'],['Evidence reference','fixture label'],
      ['Identified material','fixture insert']])
    fireEvent.change(screen.getByLabelText(label), {target:{value}})
  fireEvent.click(screen.getByRole('button',{name:'Record review and continue mission'}))
  expect(await screen.findByText(/Reviewed insert; no current demand/)).toBeVisible()
  expect(clarifyMaterial).toHaveBeenCalledWith('unknown', expect.objectContaining({version:1,disposition:'identified',
    lots:[{material:'fixture insert',condition:'dry',quantity_g:500,contaminated:false}]}), false)
})

it('recovers an existing background job after the browser session closes', async () => {
  localStorage.setItem('regen-mission', 'saved')
  localStorage.setItem('regen-job-saved', 'worker-job')
  const mission = {id:'saved', state:'planned', version:1, events:[], result:{}, inputs:{kind:'analysis'}}
  readMission.mockResolvedValue({data:mission})
  readExecutionJob.mockResolvedValue({data:{mission_id:'saved', status:'running'}})
  render(<RecoveryMission />)
  expect(await screen.findByText('Investigation: running')).toBeVisible()
  expect(readExecutionJob).toHaveBeenCalledWith('worker-job')
})
