import client from './client'
import type { MapConfig, MapConfigRequest } from '../types/api.types'

export const getMapConfig = (): Promise<MapConfig> =>
  client.get<MapConfig>('/map-config').then(r => r.data)

export const putMapConfig = (config: MapConfigRequest): Promise<MapConfig> =>
  client.put<MapConfig>('/map-config', config).then(r => r.data)
