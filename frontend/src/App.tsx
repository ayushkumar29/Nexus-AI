import React, { useState, useEffect, useCallback } from 'react';
import { MessageSquare, FolderKanban, Bot, Settings } from 'lucide-react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { DashboardOverview } from './components/dashboard/DashboardOverview';
import { PlaceholderView } from './components/common/PlaceholderView';
import type { BackendHealthState, NavigationItemKey } from './types';
import { fetchHealth } from './services/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavigationItemKey>('dashboard');
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [healthState, setHealthState] = useState<BackendHealthState>({
    status: 'connecting',
    data: null,
    error: null,
    lastChecked: null,
  });

  const checkConnection = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const data = await fetchHealth();
      setHealthState({
        status: 'connected',
        data,
        error: null,
        lastChecked: new Date().toISOString(),
      });
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : 'Unknown connection error';
      setHealthState({
        status: 'disconnected',
        data: null,
        error: errorMessage,
        lastChecked: new Date().toISOString(),
      });
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  // Poll once on mount, then periodic check every 30 seconds
  useEffect(() => {
    checkConnection();
    const interval = setInterval(() => {
      checkConnection();
    }, 30000);
    return () => clearInterval(interval);
  }, [checkConnection]);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <DashboardOverview
            healthState={healthState}
            onRetryConnection={checkConnection}
          />
        );
      case 'ai-chat':
        return (
          <PlaceholderView
            title="Nexus Intelligent Chat"
            description="Enterprise conversational AI with multi-session context, prompt management, and streaming tokens."
            icon={MessageSquare}
            badge="MILESTONE 1.2"
          />
        );
      case 'documents':
        return (
          <PlaceholderView
            title="Enterprise Knowledge Base"
            description="Upload, ingest, parse, and semantically index documents with vector embedding and hybrid search."
            icon={FolderKanban}
            badge="MILESTONE 1.3"
          />
        );
      case 'ai-agents':
        return (
          <PlaceholderView
            title="Autonomous Agents & Tools"
            description="Deploy specialized agents with tool execution, plan-and-solve loops, and external integrations."
            icon={Bot}
            badge="MILESTONE 1.4"
          />
        );
      case 'settings':
        return (
          <PlaceholderView
            title="System & LLM Configuration"
            description="Manage API endpoints, model provider credentials, temperature limits, and vector database indices."
            icon={Settings}
            badge="CORE CONFIG"
          />
        );
      default:
        return null;
    }
  };

  const isBackendHealthy =
    healthState.status === 'connected' &&
    healthState.data?.api_status === 'healthy';

  return (
    <div style={styles.appContainer}>
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        backendConnected={isBackendHealthy}
      />
      <div style={styles.mainArea}>
        <Header
          healthState={healthState}
          onRefresh={checkConnection}
          isRefreshing={isRefreshing}
        />
        <main style={styles.contentArea}>{renderContent()}</main>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  appContainer: {
    display: 'flex',
    height: '100vh',
    width: '100vw',
    overflow: 'hidden',
    backgroundColor: 'var(--bg-primary)',
  },
  mainArea: {
    display: 'flex',
    flexDirection: 'column',
    flex: 1,
    height: '100%',
    overflow: 'hidden',
  },
  contentArea: {
    flex: 1,
    overflow: 'hidden',
    backgroundColor: 'var(--bg-primary)',
  },
};

export default App;
