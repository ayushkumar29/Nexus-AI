import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface PlaceholderViewProps {
  title: string;
  description: string;
  icon: LucideIcon;
  badge: string;
}

export const PlaceholderView: React.FC<PlaceholderViewProps> = ({
  title,
  description,
  icon: Icon,
  badge,
}) => {
  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.iconCircle}>
          <Icon size={32} color="#3b82f6" />
        </div>
        <span style={styles.badge}>{badge}</span>
        <h2 style={styles.title}>{title}</h2>
        <p style={styles.description}>{description}</p>
        <div style={styles.statusNote}>
          This module will be activated in upcoming Nexus AI development phases according to architecture specification.
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '40px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
  },
  card: {
    backgroundColor: 'var(--bg-surface)',
    border: '1px solid var(--border-subtle)',
    borderRadius: '16px',
    padding: '48px 36px',
    maxWidth: '520px',
    textAlign: 'center',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '16px',
  },
  iconCircle: {
    width: '64px',
    height: '64px',
    borderRadius: '16px',
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    border: '1px solid rgba(59, 130, 246, 0.25)',
  },
  badge: {
    fontSize: '11px',
    fontWeight: 700,
    letterSpacing: '0.05em',
    padding: '3px 10px',
    borderRadius: '12px',
    backgroundColor: 'var(--bg-surface-elevated)',
    color: '#60a5fa',
    border: '1px solid rgba(59, 130, 246, 0.2)',
  },
  title: {
    fontSize: '20px',
    fontWeight: 600,
    color: 'var(--text-primary)',
  },
  description: {
    fontSize: '14px',
    color: 'var(--text-secondary)',
    lineHeight: '1.5',
  },
  statusNote: {
    marginTop: '12px',
    fontSize: '12px',
    color: 'var(--text-muted)',
    backgroundColor: 'var(--bg-primary)',
    padding: '12px 16px',
    borderRadius: '8px',
    border: '1px solid var(--border-subtle)',
    fontFamily: 'var(--font-mono)',
  },
};
