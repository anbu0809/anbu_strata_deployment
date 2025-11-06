import { useState, useEffect } from 'react';
import { X, Database, Plus, Trash2, Edit } from 'lucide-react';
import { Connection } from '../types';
import AddConnectionModal from './AddConnectionModal';

interface SettingsModalProps {
  onClose: () => void;
  connections: Connection[];
  onConnectionSaved: () => void;
  onDeleteConnection: (id: number) => void;
  editingConnectionId?: number | null;
}

const SettingsModal = ({ onClose, connections, onConnectionSaved, onDeleteConnection, editingConnectionId }: SettingsModalProps) => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingConnection, setEditingConnection] = useState<Connection | null>(null);

  // If an editingConnectionId is provided, find the connection and open the edit modal
  useEffect(() => {
    if (editingConnectionId) {
      const connectionToEdit = connections.find(conn => conn.id === editingConnectionId);
      if (connectionToEdit) {
        setEditingConnection(connectionToEdit);
        setIsAddModalOpen(true);
      }
    }
  }, [editingConnectionId, connections]);

  const handleEditConnection = (connection: Connection) => {
    setEditingConnection(connection);
    setIsAddModalOpen(true);
  };

  const handleModalClose = () => {
    setIsAddModalOpen(false);
    setEditingConnection(null);
  };

  const handleConnectionSaved = () => {
    onConnectionSaved();
    handleModalClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-[#085690]">Database Connections</h2>
            <button 
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <X className="h-5 w-5 text-gray-500" />
            </button>
          </div>
          
          <div className="mb-6">
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="flex items-center px-4 py-2 bg-[#085690] text-white rounded-md hover:bg-[#064a7a] transition-colors"
            >
              <Plus className="h-5 w-5 mr-2" />
              Add New Connection
            </button>
          </div>
          
          <div className="border-t pt-4">
            <h3 className="text-lg font-medium text-[#085690] mb-4">Existing Connections</h3>
            
            {connections.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Database className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>No database connections configured yet.</p>
                <p className="text-sm mt-2">Click "Add New Connection" to get started.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {connections.map((connection) => (
                  <div 
                    key={connection.id} 
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                  >
                    <div className="flex items-center">
                      <Database className="h-8 w-8 text-[#085690] mr-3" />
                      <div>
                        <h4 className="font-medium text-gray-900">{connection.name}</h4>
                        <p className="text-sm text-gray-500">{connection.dbType}</p>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleEditConnection(connection)}
                        className="p-2 text-[#085690] hover:bg-blue-50 rounded-full"
                        title="Edit connection"
                      >
                        <Edit className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => onDeleteConnection(connection.id)}
                        className="p-2 text-[#ec6225] hover:bg-red-50 rounded-full"
                        title="Delete connection"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
      
      {isAddModalOpen && (
        <AddConnectionModal 
          onClose={handleModalClose} 
          onConnectionSaved={handleConnectionSaved}
          editingConnection={editingConnection}
        />
      )}
    </div>
  );
};

export default SettingsModal;