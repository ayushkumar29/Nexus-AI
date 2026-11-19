import React from 'react';
import { 
  LayoutDashboard, 
  MessageSquare, 
  FolderKanban, 
  Bot, 
  Settings, 
  Cpu
} from 'lucide-react';
import type { NavigationItemKey } from '../../types';

interface SidebarProps {
  activeTab: NavigationItemKey;
  onSelectTab: (tab: NavigationItemKey) => void;
  backendConnected: boolean;
}

interface NavItem {
  key: NavigationItemKey;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { key: 'ai-chat', label: 'AI Chat', icon: MessageSquare, badge: 'M1.2' },
  { key: 'documents', label: 'Documents', icon: FolderKanban, badge: 'M1.3' },
  { key: 'ai-agents', label: 'AI Agents', icon: Bot, badge: 'M1.4' },
  { key: 'settings', label: 'Settings', icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  backendConnected,
}) => {
  return (
    <aside style={styles.sidebar}>
      <div style={styles.brand}>
        <div style={styles.logoIconContainer}>
          <Cpu size={22} color="#3b82f6" />
        </div>
        <div>
          <div style={styles.brandTitle}>Nexus AI</div>
          <div style={styles.brandSubtitle}>Knowledge Assistant</div>
        </div>
      </div>

      <nav style={styles.nav}>
        <div style={styles.sectionLabel}>WORKSPACE</div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.key;
          return (
            <button
              key={item.key}
              onClick={() => onSelectTab(item.key)}
              style={{
                ...styles.navButton,
                ...(isActive ? styles.navButtonActive : {}),
              }}
              type="button"
            >
              <div style={styles.navButtonLeft}>
                <Icon size={18} className={isActive ? 'text-blue' : ''} />
                <span style={styles.navLabel}>{item.label}</span>
              </div>
              {item.badge && (
                <span style={styles.badge}>{item.badge}</span>
              )}
            </button>
          );
        })}
      </nav>

      <div style={styles.footer}>
        <div style={styles.nodeStatus}>
          <div
            style={{
              ...styles.statusDot,
              backgroundColor: backendConnected ? 'var(--success)' : 'var(--danger)',
              boxShadow: backendConnected
                ? '0 0 8px rgba(16, 185, 129, 0.6)'
                : '0 0 8px rgba(239, 68, 68, 0.6)',
            }}
          />
          <div style={styles.statusTextContainer}>
            <div style={styles.statusTitle}>Backend API</div>
            <div style={styles.statusSubtitle}>
              {backendConnected ? '127.0.0.1:8000' : 'Disconnected'}
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    width: '260px',
    backgroundColor: 'var(--bg-surface)',
    borderRight: '1px solid var(--border-subtle)',
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    userSelect: 'none',
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '24px 20px',
    borderBottom: '1px solid var(--border-subtle)',
  },
  logoIconContainer: {
    width: '38px',
    height: '38px',
    borderRadius: '10px',
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    border: '1px solid rgba(59, 130, 246, 0.25)',
  },
  brandTitle: {
    fontSize: '16px',
    fontWeight: 700,
    letterSpacing: '-0.02em',
    color: 'var(--text-primary)',
  },
  brandSubtitle: {
    fontSize: '11px',
    color: 'var(--text-muted)',
    fontWeight: 500,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  nav: {
    padding: '16px 12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    flex: 1,
  },
  sectionLabel: {
    fontSize: '10px',
    fontWeight: 700,
    color: 'var(--text-muted)',
    letterSpacing: '0.08em',
    padding: '8px 12px 6px',
  },
  navButton: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '10px 14px',
    borderRadius: '8px',
    backgroundColor: 'transparent',
    border: 'none',
    color: 'var(--text-secondary)',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 500,
    transition: 'all 0.15s ease',
    textAlign: 'left',
    width: '100%',
  },
  navButtonActive: {
    backgroundColor: 'rgba(59, 130, 246, 0.12)',
    color: '#60a5fa',
    border: '1px solid rgba(59, 130, 246, 0.25)',
  },
  navButtonLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  navLabel: {
    fontSize: '14px',
  },
  badge: {
    fontSize: '10px',
    backgroundColor: 'var(--bg-surface-elevated)',
    color: 'var(--text-muted)',
    padding: '2px 6px',
    borderRadius: '4px',
    fontWeight: 600,
  },
  footer: {
    padding: '16px',
    borderTop: '1px solid var(--border-subtle)',
    backgroundColor: 'rgba(0, 0, 0, 0.15)',
  },
  nodeStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '10px 12px',
    backgroundColor: 'var(--bg-surface-elevated)',
    borderRadius: '8px',
    border: '1px solid var(--border-subtle)',
  },
  statusDot: {
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    flexShrink: 0,
  },
  statusTextContainer: {
    overflow: 'hidden',
  },
  statusTitle: {
    fontSize: '12px',
    fontWeight: 600,
    color: 'var(--text-primary)',
  },
  statusSubtitle: {
    fontSize: '11px',
    color: 'var(--text-muted)',
    fontFamily: 'var(--font-mono)',
  },
};
