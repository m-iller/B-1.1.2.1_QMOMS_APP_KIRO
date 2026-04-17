import { useState } from 'react'
import { createTask } from '../../api/tasks'
import type { Machine } from '../../types/api.types'

interface Props { machines: Machine[]; onCreated: () => void }

export function CreateTaskForm({ machines, onCreated }: Props) {
  const [machineId, setMachineId] = useState('')
  const [title, setTitle] = useState('')
  const [priority, setPriority] = useState('medium')
  const [deadline, setDeadline] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setPending(true)
    try {
      await createTask({ machine_id: machineId, title, priority, deadline })
      setTitle(''); setMachineId(''); setDeadline('')
      onCreated()
    } catch {
      setError('Failed to create task')
    } finally {
      setPending(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: 16 }}>
      <select value={machineId} onChange={e => setMachineId(e.target.value)} required style={{ padding: 6 }}>
        <option value="">Select machine</option>
        {machines.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
      </select>
      <input placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} required style={{ padding: 6 }} />
      <select value={priority} onChange={e => setPriority(e.target.value)} style={{ padding: 6 }}>
        {['low', 'medium', 'high', 'critical'].map(p => <option key={p}>{p}</option>)}
      </select>
      <input type="datetime-local" value={deadline} onChange={e => setDeadline(e.target.value)} required style={{ padding: 6 }} />
      <button type="submit" disabled={pending} style={{ padding: '6px 16px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 4 }}>
        {pending ? 'Creating...' : 'Create Task'}
      </button>
      {error && <span style={{ color: '#dc2626' }}>{error}</span>}
    </form>
  )
}
