import { usePolling } from '../../hooks/usePolling'
import { getTasks } from '../../api/tasks'
import { getMachines } from '../../api/machines'
import { TaskTable } from './TaskTable'
import { CreateTaskForm } from './CreateTaskForm'
import { ErrorBanner } from '../../components/ErrorBanner'

export function TaskPanelPage() {
  const { data: tasks, error, loading, refresh } = usePolling(getTasks, 7000)
  const { data: machines } = usePolling(getMachines, 7000)

  return (
    <div>
      <h2>Task Panel</h2>
      <ErrorBanner error={error} />
      <CreateTaskForm machines={machines ?? []} onCreated={refresh} />
      {loading && <p>Loading tasks...</p>}
      <TaskTable tasks={tasks ?? []} onRefresh={refresh} />
    </div>
  )
}
