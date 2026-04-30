import { useState, useCallback, useEffect } from 'react'
import { getMachines, createMachine, deleteMachine, updateMachineConfig } from '../../api/machines'
import { ErrorBanner } from '../../components/ErrorBanner'
import type { Machine } from '../../types/api.types'
import { useAuth } from '../../context/AuthContext'

const ALL_SENSORS = ['engine_temp', 'fuel_level', 'speed', 'payload_weight']
const MACHINE_TYPES = ['excavator', 'haul_truck', 'drill', 'dozer', 'grader']
const ADMIN_ROLES = ['admin', 'dev']

export function MachineryPage() {
  const { user } = useAuth()
  const canAdmin = ADMIN_ROLES.includes(user?.role ?? '')
  const canEdit = ['admin', 'dispatcher', 'dev'].includes(user?.role ?? '')

  const [machines, setMachines] = useState<Machine[]>([])
  const [error, setError] = useState<unknown>(null)
  const [loading, setLoading] = useState(true)

  // Add form state
  const [addName, setAddName] = useState('')
  const [addType, setAddType] = useState('excavator')
  const [addDesc, setAddDesc] = useState('')
  const [addSensors, setAddSensors] = useState<string[]>([...ALL_SENSORS])
  const [adding, setAdding] = useState(false)
  const [addError, setAddError] = useState('')

  // Edit state: machineId -> {description, enabled_sensors}
  const [editState, setEditState] = useState<Record<string, { description: string; sensors: string[] }>>({})
  const [savingId, setSavingId] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const data = await getMachines()
      setMachines(data)
      // Init edit state — only set for machines not yet tracked to avoid overwriting in-progress edits
      setEditState(prev => {
        const next = { ...prev }
        for (const m of data) {
          if (!next[m.id]) {
            next[m.id] = { description: m.description ?? '', sensors: m.enabled_sensors ?? [...ALL_SENSORS] }
          }
        }
        return next
      })
      setError(null)
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])  // stable — no deps, load never changes

  useEffect(() => { load() }, [load])

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!addName.trim()) return
    setAdding(true)
    setAddError('')
    try {
      await createMachine({ name: addName.trim(), type: addType, description: addDesc || undefined, enabled_sensors: addSensors })
      setAddName('')
      setAddDesc('')
      setAddSensors([...ALL_SENSORS])
      await load()
    } catch (err: any) {
      setAddError(err?.response?.data?.message ?? 'Failed to add machine')
    } finally {
      setAdding(false)
    }
  }

  const handleDelete = async (id: string) => {
    setDeletingId(id)
    try {
      await deleteMachine(id)
      await load()
    } finally {
      setDeletingId(null)
    }
  }

  const handleSaveConfig = async (id: string) => {
    const state = editState[id]
    if (!state) return
    setSavingId(id)
    try {
      await updateMachineConfig(id, { description: state.description || undefined, enabled_sensors: state.sensors })
      await load()
    } finally {
      setSavingId(null)
    }
  }

  const toggleSensor = (machineId: string, sensor: string) => {
    setEditState(prev => {
      const current = prev[machineId]?.sensors ?? [...ALL_SENSORS]
      const updated = current.includes(sensor)
        ? current.filter(s => s !== sensor)
        : [...current, sensor]
      return { ...prev, [machineId]: { ...prev[machineId], sensors: updated } }
    })
  }

  const toggleAddSensor = (sensor: string) => {
    setAddSensors(prev =>
      prev.includes(sensor) ? prev.filter(s => s !== sensor) : [...prev, sensor]
    )
  }

  return (
    <div>
      <h2>Machinery Control</h2>
      <ErrorBanner error={error} />

      {/* Add machine form */}
      {canEdit && (
        <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, marginBottom: 24 }}>
          <h4 style={{ margin: '0 0 12px' }}>Add Machine</h4>
          <form onSubmit={handleAdd}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
              <label style={{ fontSize: 13 }}>
                Name *
                <input
                  value={addName}
                  onChange={e => setAddName(e.target.value)}
                  required
                  style={{ display: 'block', width: '100%', padding: '5px 8px', marginTop: 3, border: '1px solid #d1d5db', borderRadius: 4 }}
                />
              </label>
              <label style={{ fontSize: 13 }}>
                Type
                <select
                  value={addType}
                  onChange={e => setAddType(e.target.value)}
                  style={{ display: 'block', width: '100%', padding: '5px 8px', marginTop: 3, border: '1px solid #d1d5db', borderRadius: 4 }}
                >
                  {MACHINE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </label>
            </div>
            <label style={{ fontSize: 13, display: 'block', marginBottom: 10 }}>
              Description
              <input
                value={addDesc}
                onChange={e => setAddDesc(e.target.value)}
                placeholder="Optional description"
                style={{ display: 'block', width: '100%', padding: '5px 8px', marginTop: 3, border: '1px solid #d1d5db', borderRadius: 4 }}
              />
            </label>
            <div style={{ fontSize: 13, marginBottom: 12 }}>
              <strong>Enabled Sensors:</strong>
              <div style={{ display: 'flex', gap: 12, marginTop: 6, flexWrap: 'wrap' }}>
                {ALL_SENSORS.map(s => (
                  <label key={s} style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer', fontSize: 13 }}>
                    <input type="checkbox" checked={addSensors.includes(s)} onChange={() => toggleAddSensor(s)} />
                    {s}
                  </label>
                ))}
              </div>
            </div>
            {addError && <p style={{ color: '#dc2626', fontSize: 12, margin: '0 0 8px' }}>{addError}</p>}
            <button
              type="submit"
              disabled={adding}
              style={{ padding: '6px 16px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6, cursor: adding ? 'not-allowed' : 'pointer', fontSize: 13 }}
            >
              {adding ? 'Adding...' : '+ Add Machine'}
            </button>
          </form>
        </div>
      )}

      {/* Machine list */}
      {loading && <p style={{ color: '#6b7280' }}>Loading...</p>}
      {machines.map(machine => {
        const edit = editState[machine.id] ?? { description: machine.description ?? '', sensors: machine.enabled_sensors ?? ALL_SENSORS }
        const isDirty =
          edit.description !== (machine.description ?? '') ||
          JSON.stringify([...edit.sensors].sort()) !== JSON.stringify([...(machine.enabled_sensors ?? ALL_SENSORS)].sort())

        return (
          <div key={machine.id} style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, marginBottom: 12, background: '#fff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <strong style={{ fontSize: 15 }}>{machine.name}</strong>
                <span style={{ marginLeft: 8, fontSize: 12, color: '#6b7280', background: '#f3f4f6', padding: '2px 6px', borderRadius: 4 }}>{machine.type}</span>
                <span style={{ marginLeft: 8, fontSize: 12, color: '#6b7280' }}>State: {machine.current_state}</span>
              </div>
              {canAdmin && (
                <button
                  onClick={() => handleDelete(machine.id)}
                  disabled={deletingId === machine.id}
                  style={{ padding: '4px 10px', fontSize: 12, background: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5', borderRadius: 4, cursor: 'pointer' }}
                >
                  {deletingId === machine.id ? '...' : 'Delete'}
                </button>
              )}
            </div>

            <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>ID: {machine.id}</div>

            {canEdit && (
              <div style={{ marginTop: 12 }}>
                <label style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>
                  Description
                  <input
                    value={edit.description}
                    onChange={e => setEditState(prev => ({ ...prev, [machine.id]: { ...prev[machine.id], description: e.target.value } }))}
                    placeholder="Add description..."
                    style={{ display: 'block', width: '100%', padding: '4px 8px', marginTop: 3, border: '1px solid #d1d5db', borderRadius: 4, fontSize: 13 }}
                  />
                </label>

                <div style={{ fontSize: 13, marginBottom: 8 }}>
                  <strong>Displayed Sensors:</strong>
                  <div style={{ display: 'flex', gap: 12, marginTop: 6, flexWrap: 'wrap' }}>
                    {ALL_SENSORS.map(s => (
                      <label key={s} style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer', fontSize: 13 }}>
                        <input
                          type="checkbox"
                          checked={edit.sensors.includes(s)}
                          onChange={() => toggleSensor(machine.id, s)}
                        />
                        {s}
                      </label>
                    ))}
                  </div>
                </div>

                {isDirty && (
                  <button
                    onClick={() => handleSaveConfig(machine.id)}
                    disabled={savingId === machine.id}
                    style={{ padding: '4px 12px', fontSize: 12, background: '#2563eb', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}
                  >
                    {savingId === machine.id ? 'Saving...' : 'Save Changes'}
                  </button>
                )}
              </div>
            )}

            {!canEdit && machine.description && (
              <p style={{ fontSize: 13, color: '#374151', marginTop: 8 }}>{machine.description}</p>
            )}
          </div>
        )
      })}
    </div>
  )
}
