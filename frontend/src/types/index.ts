export interface HealthResponse {
  application_name: string;
  api_status: 'healthy' | 'degraded' | 'unhealthy';
  application_version: string;
  environment: string;
  timestamp: string;
  details?: string;
}

export type ConnectionState = 'connected' | 'connecting' | 'disconnected';

export interface BackendHealthState {
  status: ConnectionState;
  data: HealthResponse | null;
  error: string | null;
  lastChecked: string | null;
}

export type NavigationItemKey =
  | 'dashboard'
  | 'ai-chat'
  | 'documents'
  | 'ai-agents'
  | 'settings';
