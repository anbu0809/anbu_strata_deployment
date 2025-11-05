import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import Dashboard from './pages/Dashboard';
import Analyze from './pages/Analyze';
import Extract from './pages/Extract';
import Migrate from './pages/Migrate';
import Reconcile from './pages/Reconcile';
import SettingsModal from './components/SettingsModal';
import { Connection } from './types';

function App() {
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [connections, setConnections] = useState<Connection[]>([]);

  // Fetch connections on app load
  useEffect(() => {
    fetchConnections();
  }, []);

  const fetchConnections = async () => {
    try {
      const response = await fetch('/api/connections');
      if (response.ok) {
        const data = await response.json();
        setConnections(data);
      }
    } catch (error) {
      console.error('Failed to fetch connections:', error);
    }
  };

  const deleteConnection = async (connectionId: number) => {
    try {
      const response = await fetch(`/api/connections/${connectionId}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        // Refresh the connections list
        fetchConnections();
      }
    } catch (error) {
      console.error('Failed to delete connection:', error);
    }
  };

  const [editingConnectionId, setEditingConnectionId] = useState<number | null>(null);

  const openSettingsModal = () => setIsSettingsModalOpen(true);
  const closeSettingsModal = () => setIsSettingsModalOpen(false);

  return (
    <Router>
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <div className="flex flex-col flex-1 overflow-hidden">
          <TopBar onSettingsClick={openSettingsModal} />
          <main className="flex-1 overflow-y-auto p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/analyze" element={<Analyze connections={connections} />} />
              <Route path="/extract" element={<Extract />} />
              <Route path="/migrate" element={<Migrate />} />
              <Route path="/reconcile" element={<Reconcile />} />
            </Routes>
          </main>
        </div>
        {isSettingsModalOpen && (
          <SettingsModal 
            onClose={() => {
              closeSettingsModal();
              setEditingConnectionId(null);
            }}
            connections={connections}
            onConnectionSaved={fetchConnections}
            onDeleteConnection={deleteConnection}
            editingConnectionId={editingConnectionId}
          />
        )}
      </div>
    </Router>
  );
}

export default App;