import type { Task } from '../../types/api.types'
import { OverdueBadge } from '../../components/OverdueBadge'

interface Props { tasks: Task[] }

export function TaskTable({ tasks }: Props) {
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <thead>
        <tr style={{ background: '#f9fafb' }}>
          {['Title', 'Machine', 'Priority', 'State', 'Deadline', ''].map(h => (
            <th key={h} style={{ padding: '8px 12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {tasks.map(t => (
          <tr key={t.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
            <td style={{ padding: '8px 12px' }}>{t.title}</td>
            <td style={{ padding: '8px 12px', fontSize: 13, color: '#6b7280' }}>{t.machine_id}</td>
            <td style={{ padding: '8px 12px' }}>{t.priority}</td>
            <td style={{ padding: '8px 12px' }}>{t.state}{t.pending_activation && ' (pending)'}</td>
            <td style={{ padding: '8px 12px', fontSize: 13 }}>{new Date(t.deadline).toLocaleDateString()}</td>
            <td style={{ padding: '8px 12px' }}>{t.overdue && <OverdueBadge />}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
