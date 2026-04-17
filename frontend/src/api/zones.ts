import client from './client'
import type { Zone } from '../types/api.types'

export const getZones = () => client.get<Zone[]>('/zones').then(r => r.data)
