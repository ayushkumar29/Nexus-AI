import React from 'react';
import { RefreshCw, Server, AlertTriangle } from 'lucide-react';
import type { BackendHealthState } from '../../types';

interface HeaderProps {
  healthState: BackendHealthState;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  healthState,
  onRefresh,
  isRefreshing,
}) => {
  const isHealthy = healthState.status === 'connected' && healthState.data?.api_status === 'healthy';

  return (
    <header style={styles.header}>
      <div style={styles.headerLeft}>
        <h1 style={styles.title}>System Control Center</h1>
        <span style={styles.subtitle}>Enterprise Intelligence Engine</span>
      </div>

      <div style={styles.headerRight}>
        <div style={styles.statusPill}>
          {isHealthy ? (
            <Server size={14} color="var(--success)" />
          ) : (
            <AlertTriangle size={14} color={healthState.status === 'connecting' ? 'var(--warning)' : 'var(--danger)'} />
          )}
          <span style={styles.statusPillText}>
            {healthState.status === 'connecting'
              ? 'Checking status...'
              : isHealthy
              ? 'Core API Online'
              : 'Service Unavailable'}
          </span>
        </div>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          style={{
            ...styles.refreshBtn,
            opacity: isRefreshing ? 0.6 : 1,
            cursor: isRefreshing ? 'not-allowed' : 'pointer',
          }}
          title="Poll backend health"
          type="button"
        >
          <RefreshCw
            size={14}
            style={{
              animation: isRefreshing ? 'spin 1s linear infinite' : 'none',
            }}
          />
          <span>{isRefreshing ? 'Checking...' : 'Refresh'}</span>
        </button>
      </div>
    </header>
  );
};

const styles: Record<string, React.CSSProperties> = {
  header: {
    height: '64px',
    backgroundColor: 'var(--bg-surface)',
    borderBottom: '1px solid var(--border-subtle)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 32px',
    flexShrink: 0,
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'baseline',
    gap: '12px',
  },
  title: {
    fontSize: '18px',
    fontWeight: 600,
    color: 'var(--text-primary)',
    letterSpacing: '-0.02em',
  },
  subtitle: {
    fontSize: '12px',
    color: 'var(--text-muted)',
    fontWeight: 400,
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  statusPill: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '6px 12px',
    borderRadius: '20px',
    backgroundColor: 'var(--bg-surface-elevated)',
    border: '1px solid var(--border-subtle)',
    fontSize: '12px',
    fontWeight: 500,
    color: 'var(--text-secondary)',
  },
  statusPillText: {
    fontSize: '12px',
  },
  refreshBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '7px 14px',
    borderRadius: '6px',
    backgroundColor: 'var(--bg-surface-elevated)',
    border: '1px solid var(--border-strong)',
    color: 'var(--text-primary)',
    fontSize: '12px',
    fontWeight: 500,
    transition: 'background-color 0.15s ease',
  },
};
