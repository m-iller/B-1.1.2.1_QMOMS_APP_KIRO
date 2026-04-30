import { useState } from 'react'
import type { Task } from '../../types/api.types'
import { OverdueBadge } from '../../components/OverdueBadge'
import { deleteTask } from '../../api/tasks'
import { usePermissions } from '../../context/PermissionsContext'

interface Props {
  tasks: Task[]
  onRefresh: () => void
}

export function TaskTable({ tasks, onRefresh }: Props) {
  const { canDo } = usePermissions()
  const canDelete = canDo('tasks.delete')
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleDelete = async (taskId: string) => {
    setDeletingId(taskId)
    try {
      await deleteTask(taskId)
      onRefresh()
    } finally {
      setDeletingId(null)
    }
  }

  const headers = ['Title', 'Machine', 'Priority', 'State', 'Deadline', '', ...(canDelete ? [''] : [])]

  return (
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <thead>
        <tr style={{ background: '#f9fafb' }}>
          {headers.map((h, i) => (
            <th key={i} style={{ padding: '8px 12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {tasks.map(task => (
          <tr key={task.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
            <td style={{ padding: '8px 12px' }}>{task.title}</td>
            <td style={{ padding: '8px 12px', fontSize: 13, color: '#6b7280' }}>{task.machine_id}</td>
            <td style={{ padding: '8px 12px' }}>{task.priority}</td>
            <td style={{ padding: '8px 12px' }}>{task.state}{task.pending_activation && ' (pending)'}</td>
            <td style={{ padding: '8px 12px', fontSize: 13 }}>{new Date(task.deadline).toLocaleDateString()}</td>
            <td style={{ padding: '8px 12px' }}>{task.overdue && <OverdueBadge />}</td>
            {canDelete && (
              <td style={{ padding: '8px 12px' }}>
                <button
                  onClick={() => handleDelete(task.id)}
                  disabled={deletingId === task.id}
                  style={{
                    padding: '3px 10px',
                    fontSize: 12,
                    background: '#fee2e2',
                    color: '#991b1b',
                    border: '1px solid #fca5a5',
                    borderRadius: 4,
                    cursor: deletingId === task.id ? 'not-allowed' : 'pointer',
                  }}
                >
                  {deletingId === task.id ? '...' : 'Delete'}
                </button>
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
