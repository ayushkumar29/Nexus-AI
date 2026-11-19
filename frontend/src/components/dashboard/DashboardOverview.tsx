import React from 'react';
import { 
  Activity, 
  Layers, 
  Terminal, 
  ShieldCheck, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  Code
} from 'lucide-react';
import type { BackendHealthState } from '../../types';
import { MetricCard } from './MetricCard';

interface DashboardOverviewProps {
  healthState: BackendHealthState;
  onRetryConnection: () => void;
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({
  healthState,
  onRetryConnection,
}) => {
  const { status, data, error, lastChecked } = healthState;
  const isConnected = status === 'connected' && data !== null;

  return (
    <div style={styles.container}>
      {/* Welcome & Overview Header */}
      <div style={styles.pageHeader}>
        <div>
          <h2 style={styles.heading}>System Overview</h2>
          <p style={styles.description}>
            Live telemetry and operational readiness of Nexus AI infrastructure.
          </p>
        </div>
      </div>

      {/* Backend Connection Alert if failed */}
      {status === 'disconnected' && (
        <div style={styles.errorBanner}>
          <div style={styles.errorBannerContent}>
            <AlertCircle size={20} color="var(--danger)" />
            <div>
              <div style={styles.errorTitle}>Backend Connection Failed</div>
              <div style={styles.errorMessage}>
                {error || 'Unable to establish HTTP handshake with the FastAPI backend service.'}
              </div>
            </div>
          </div>
          <button onClick={onRetryConnection} style={styles.retryButton} type="button">
            Retry Connection
          </button>
        </div>
      )}

      {/* Key Metrics Grid */}
      <div style={styles.metricsGrid}>
        <MetricCard
          title="Core API Status"
          value={
            status === 'connecting'
              ? 'Checking...'
              : isConnected
              ? (data?.api_status || 'Unknown').toUpperCase()
              : 'OFFLINE'
          }
          subtitle={isConnected ? `Diagnostic: ${data?.details || 'Normal'}` : 'Backend unreachable'}
          badge={isConnected ? 'Operational' : 'Critical'}
          badgeVariant={isConnected ? 'success' : 'danger'}
          icon={Activity}
        />

        <MetricCard
          title="App Version"
          value={isConnected ? `v${data?.application_version}` : '--'}
          subtitle={isConnected ? `Service: ${data?.application_name}` : 'Awaiting handshake'}
          badge="Release"
          badgeVariant="info"
          icon={Layers}
        />

        <MetricCard
          title="Active Environment"
          value={isConnected ? (data?.environment || '').toUpperCase() : '--'}
          subtitle="Host: 127.0.0.1:8000"
          badge={isConnected ? 'Local' : 'Inactive'}
          badgeVariant={isConnected ? 'info' : 'warning'}
          icon={Terminal}
        />

        <MetricCard
          title="Security & CORS"
          value="ENFORCED"
          subtitle="Strict origin validation active"
          badge="Active"
          badgeVariant="success"
          icon={ShieldCheck}
        />
      </div>

      {/* Detailed Diagnostics Section */}
      <div style={styles.diagnosticsSection}>
        <div style={styles.sectionHeader}>
          <h3 style={styles.sectionTitle}>Runtime Diagnostics & Response Payload</h3>
          <span style={styles.timestampBadge}>
            <Clock size={12} />
            Last Synced: {lastChecked ? new Date(lastChecked).toLocaleTimeString() : 'Never'}
          </span>
        </div>

        <div style={styles.splitPanel}>
          {/* Status Breakdown */}
          <div style={styles.panelCard}>
            <div style={styles.panelTitle}>Endpoint Telemetry (/api/v1/health)</div>
            <div style={styles.telemetryList}>
              <div style={styles.telemetryItem}>
                <span style={styles.telemetryLabel}>Target URL</span>
                <span style={styles.telemetryValue}>
                  {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/health
                </span>
              </div>
              <div style={styles.telemetryItem}>
                <span style={styles.telemetryLabel}>HTTP Status</span>
                <span style={styles.telemetryValue}>
                  {isConnected ? (
                    <span style={{ color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <CheckCircle2 size={14} /> 200 OK
                    </span>
                  ) : (
                    <span style={{ color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <AlertCircle size={14} /> Connection Refused / Error
                    </span>
                  )}
                </span>
              </div>
              <div style={styles.telemetryItem}>
                <span style={styles.telemetryLabel}>Payload Protocol</span>
                <span style={styles.telemetryValue}>JSON (Pydantic validated)</span>
              </div>
              <div style={styles.telemetryItem}>
                <span style={styles.telemetryLabel}>Server Architecture</span>
                <span style={styles.telemetryValue}>FastAPI + Uvicorn ASGI</span>
              </div>
            </div>
          </div>

          {/* Raw JSON viewer */}
          <div style={styles.panelCard}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={styles.panelTitle}>
                <Code size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                Raw Backend Payload
              </div>
              <span style={styles.codeTag}>GET 200</span>
            </div>
            <pre style={styles.codeBlock}>
              {isConnected
                ? JSON.stringify(data, null, 2)
                : JSON.stringify(
                    {
                      status: 'error',
                      message: error || 'No connection established to backend server.',
                      resolution: 'Ensure FastAPI backend is running via .venv/Scripts/python run.py',
                    },
                    null,
                    2
                  )}
            </pre>
          </div>
        </div>
      </div>

      {/* Planned Roadmap Cards */}
      <div style={styles.roadmapSection}>
        <h3 style={styles.sectionTitle}>Nexus AI Milestone Roadmap</h3>
        <div style={styles.roadmapGrid}>
          <div style={{ ...styles.roadmapCard, borderLeft: '3px solid var(--success)' }}>
            <div style={styles.roadmapStatus}>COMPLETED</div>
            <div style={styles.roadmapCardTitle}>M1.1 Full-Stack Core Setup</div>
            <p style={styles.roadmapText}>
              Modular FastAPI backend, configuration, centralized exceptions, React + TS dashboard, and health monitoring.
            </p>
          </div>
          <div style={{ ...styles.roadmapCard, borderLeft: '3px solid var(--accent-primary)' }}>
            <div style={{ ...styles.roadmapStatus, color: 'var(--accent-primary)' }}>NEXT UP</div>
            <div style={styles.roadmapCardTitle}>M1.2 Intelligent AI Chat</div>
            <p style={styles.roadmapText}>
              Streaming chat completions, token metrics, multi-session management, and prompt templating.
            </p>
          </div>
          <div style={{ ...styles.roadmapCard, borderLeft: '3px solid var(--text-muted)' }}>
            <div style={{ ...styles.roadmapStatus, color: 'var(--text-muted)' }}>PLANNED</div>
            <div style={styles.roadmapCardTitle}>M1.3 Knowledge Documents (RAG)</div>
            <p style={styles.roadmapText}>
              Chunking pipelines, vector store indexing, document retrieval, and grounded contextual synthesis.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '32px',
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
    overflowY: 'auto',
    height: '100%',
  },
  pageHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  heading: {
    fontSize: '22px',
    fontWeight: 700,
    letterSpacing: '-0.02em',
    color: 'var(--text-primary)',
  },
  description: {
    fontSize: '14px',
    color: 'var(--text-secondary)',
    marginTop: '4px',
  },
  errorBanner: {
    backgroundColor: 'var(--danger-bg)',
    border: '1px solid rgba(239, 68, 68, 0.4)',
    borderRadius: '10px',
    padding: '16px 20px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  errorBannerContent: {
    display: 'flex',
    alignItems: 'center',
    gap: '14px',
  },
  errorTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#f87171',
  },
  errorMessage: {
    fontSize: '13px',
    color: '#fca5a5',
    marginTop: '2px',
  },
  retryButton: {
    backgroundColor: '#dc2626',
    color: '#ffffff',
    border: 'none',
    padding: '8px 16px',
    borderRadius: '6px',
    fontSize: '12px',
    fontWeight: 600,
    cursor: 'pointer',
    flexShrink: 0,
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: '16px',
  },
  diagnosticsSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '14px',
  },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: '16px',
    fontWeight: 600,
    color: 'var(--text-primary)',
  },
  timestampBadge: {
    fontSize: '12px',
    color: 'var(--text-muted)',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  splitPanel: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
    gap: '16px',
  },
  panelCard: {
    backgroundColor: 'var(--bg-surface)',
    border: '1px solid var(--border-subtle)',
    borderRadius: '12px',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column',
  },
  panelTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: 'var(--text-secondary)',
    marginBottom: '16px',
  },
  telemetryList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  telemetryItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: '10px',
    borderBottom: '1px solid var(--border-subtle)',
    fontSize: '13px',
  },
  telemetryLabel: {
    color: 'var(--text-muted)',
  },
  telemetryValue: {
    color: 'var(--text-primary)',
    fontWeight: 500,
    fontFamily: 'var(--font-mono)',
    fontSize: '12px',
  },
  codeTag: {
    fontSize: '11px',
    backgroundColor: 'var(--bg-surface-elevated)',
    color: 'var(--accent-cyan)',
    padding: '2px 8px',
    borderRadius: '4px',
    fontFamily: 'var(--font-mono)',
  },
  codeBlock: {
    backgroundColor: 'var(--bg-primary)',
    border: '1px solid var(--border-subtle)',
    borderRadius: '8px',
    padding: '14px',
    fontSize: '12px',
    fontFamily: 'var(--font-mono)',
    color: '#e2e8f0',
    overflowX: 'auto',
    flex: 1,
    lineHeight: '1.5',
  },
  roadmapSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '14px',
    marginTop: '8px',
  },
  roadmapGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '16px',
  },
  roadmapCard: {
    backgroundColor: 'var(--bg-surface)',
    border: '1px solid var(--border-subtle)',
    borderRadius: '10px',
    padding: '16px 20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  roadmapStatus: {
    fontSize: '10px',
    fontWeight: 700,
    color: 'var(--success)',
    letterSpacing: '0.08em',
  },
  roadmapCardTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: 'var(--text-primary)',
  },
  roadmapText: {
    fontSize: '12px',
    color: 'var(--text-secondary)',
    lineHeight: '1.4',
  },
};
