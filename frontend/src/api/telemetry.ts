import client from './client'
import type { TelemetryRecord } from '../types/api.types'

export const getLatestTelemetry = (machineId: string) =>
  client.get<TelemetryRecord[]>(`/telemetry/${machineId}/latest`).then(r => r.data)
