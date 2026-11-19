import React from 'react';

interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  badge?: string;
  badgeVariant?: 'success' | 'warning' | 'danger' | 'info';
  icon: React.ComponentType<{ size?: number; color?: string; style?: React.CSSProperties }>;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  badge,
  badgeVariant = 'info',
  icon: Icon,
}) => {
  const getBadgeStyle = () => {
    switch (badgeVariant) {
      case 'success':
        return { backgroundColor: 'var(--success-bg)', color: 'var(--success)' };
      case 'warning':
        return { backgroundColor: 'var(--warning-bg)', color: 'var(--warning)' };
      case 'danger':
        return { backgroundColor: 'var(--danger-bg)', color: 'var(--danger)' };
      default:
        return { backgroundColor: 'rgba(59, 130, 246, 0.12)', color: '#60a5fa' };
    }
  };

  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <span style={styles.title}>{title}</span>
        <div style={styles.iconContainer}>
          <Icon size={18} color="#9ca3af" />
        </div>
      </div>
      <div style={styles.body}>
        <div style={styles.valueRow}>
          <div style={styles.value}>{value}</div>
          {badge && <span style={{ ...styles.badge, ...getBadgeStyle() }}>{badge}</span>}
        </div>
        {subtitle && <div style={styles.subtitle}>{subtitle}</div>}
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  card: {
    backgroundColor: 'var(--bg-surface)',
    borderRadius: '12px',
    border: '1px solid var(--border-subtle)',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    minHeight: '130px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
  },
  title: {
    fontSize: '13px',
    fontWeight: 500,
    color: 'var(--text-secondary)',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  },
  iconContainer: {
    width: '32px',
    height: '32px',
    borderRadius: '8px',
    backgroundColor: 'var(--bg-surface-elevated)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  body: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  valueRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  value: {
    fontSize: '24px',
    fontWeight: 700,
    color: 'var(--text-primary)',
    letterSpacing: '-0.02em',
  },
  badge: {
    fontSize: '11px',
    fontWeight: 600,
    padding: '2px 8px',
    borderRadius: '12px',
    textTransform: 'uppercase',
  },
  subtitle: {
    fontSize: '12px',
    color: 'var(--text-muted)',
  },
};
