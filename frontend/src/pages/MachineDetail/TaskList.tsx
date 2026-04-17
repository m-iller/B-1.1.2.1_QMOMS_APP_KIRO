import type { Task } from '../../types/api.types'
import { OverdueBadge } from '../../components/OverdueBadge'

interface Props { tasks: Task[] }

export function TaskList({ tasks }: Props) {
  return (
    <div>
      <h4>Tasks</h4>
      {tasks.length === 0 && <p style={{ color: '#6b7280' }}>No tasks assigned</p>}
      {tasks.map(t => (
        <div key={t.id} style={{ border: '1px solid #e5e7eb', borderRadius: 6, padding: 12, marginBottom: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <strong>{t.title}</strong>
            {t.overdue && <OverdueBadge />}
          </div>
          <div style={{ color: '#6b7280', fontSize: 13 }}>{t.state} · {t.priority}</div>
        </div>
      ))}
    </div>
  )
}
