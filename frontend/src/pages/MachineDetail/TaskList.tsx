import { useState } from 'react'
import type { Task } from '../../types/api.types'
import { OverdueBadge } from '../../components/OverdueBadge'
import { deleteTask } from '../../api/tasks'
import { usePermissions } from '../../context/PermissionsContext'

interface Props {
  tasks: Task[]
  onRefresh: () => void
}

const STATE_COLORS: Record<string, string> = {
  pending: '#f3f4f6',
  active: '#eff6ff',
  completed: '#f0fdf4',
  validated: '#dcfce7',
}

export function TaskList({ tasks, onRefresh }: Props) {
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

  return (
    <div>
      <h4>Tasks</h4>
      {tasks.length === 0 && <p style={{ color: '#6b7280' }}>No tasks assigned</p>}
      {tasks.map(task => (
        <div
          key={task.id}
          style={{
            border: '1px solid #e5e7eb',
            borderRadius: 6,
            padding: 12,
            marginBottom: 8,
            background: STATE_COLORS[task.state] ?? '#f9fafb',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <strong>{task.title}</strong>
              {task.overdue && <OverdueBadge />}
              <div style={{ color: '#6b7280', fontSize: 13, marginTop: 2 }}>
                {task.state} · {task.priority}
                {task.description && (
                  <span style={{ marginLeft: 8, color: '#9ca3af' }}>{task.description}</span>
                )}
              </div>
            </div>
            {canDelete && (
              <button
                onClick={() => handleDelete(task.id)}
                disabled={deletingId === task.id}
                style={{
                  marginLeft: 8,
                  padding: '3px 10px',
                  fontSize: 12,
                  background: '#fee2e2',
                  color: '#991b1b',
                  border: '1px solid #fca5a5',
                  borderRadius: 4,
                  cursor: deletingId === task.id ? 'not-allowed' : 'pointer',
                  flexShrink: 0,
                }}
              >
                {deletingId === task.id ? '...' : 'Delete'}
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
