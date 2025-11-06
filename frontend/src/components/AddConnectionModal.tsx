import React, { useState, useEffect } from 'react';
import { X, Database, Server, Key, User, Hash, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { DatabaseType, Connection } from '../types';

interface AddConnectionModalProps {
  onClose: () => void;
  onConnectionSaved: () => void;
  editingConnection?: Connection | null;
}

const databaseTypes: DatabaseType[] = [
  'PostgreSQL',
  'MySQL',
  'Snowflake',
  'Databricks',
  'Oracle',
  'SQL Server',
  'Teradata',
  'Google BigQuery'
];

const AddConnectionModal = ({ onClose, onConnectionSaved, editingConnection }: AddConnectionModalProps) => {
  const [connectionName, setConnectionName] = useState('');
  const [databaseType, setDatabaseType] = useState<DatabaseType>('PostgreSQL');
  const [credentials, setCredentials] = useState<Record<string, string>>({});
  const [isTesting, setIsTesting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message?: string } | null>(null);

  // Populate form when editing a connection
  useEffect(() => {
    if (editingConnection) {
      setConnectionName(editingConnection.name);
      setDatabaseType(editingConnection.dbType as DatabaseType);
      // Fetch full connection details for credentials
      fetchConnectionDetails(editingConnection.id);
    } else {
      // Reset form for new connection
      setConnectionName('');
      setDatabaseType('PostgreSQL');
      setCredentials({});
      setTestResult(null);
    }
  }, [editingConnection]);

  const fetchConnectionDetails = async (connectionId: number) => {
    try {
      const response = await fetch(`/api/connections/${connectionId}`);
      if (response.ok) {
        const connection = await response.json();
        setCredentials(connection.credentials || {});
      }
    } catch (error) {
      console.error('Failed to fetch connection details:', error);
    }
  };

  // Define credential fields for each database type
  const credentialFields: Record<DatabaseType, { name: string; label: string; type: string; icon: React.ReactNode }[]> = {
    'PostgreSQL': [
      { name: 'host', label: 'Host', type: 'text', icon: <Server className="h-4 w-4" /> },
      { name: 'port', label: 'Port', type: 'number', icon: <Hash className="h-4 w-4" /> },
      { name: 'database', label: 'Database', type: 'text', icon: <Database className="h-4 w-4" /> },
      { name: 'username', label: 'Username', type: 'text', icon: <User className="h-4 w-4" /> },
      { name: 'password', label: 'Password', type: 'password', icon: <Key className="h-4 w-4" /> },
      { name: 'sslmode', label: 'SSL Mode', type: 'select', icon: <FileText className="h-4 w-4" /> }
    ],
    'MySQL': [
      { name: 'host', label: 'Host', type: 'text', icon: <Server className="h-4 w-4" /> },
      { name: 'port', label: 'Port', type: 'number', icon: <Hash className="h-4 w-4" /> },
      { name: 'database', label: 'Database', type: 'text', icon: <Database className="h-4 w-4" /> },
      { name: 'username', label: 'Username', type: 'text', icon: <User className="h-4 w-4" /> },
      { name: 'password', label: 'Password', type: 'password', icon: <Key className="h-4 w-4" /> },
      { name: 'ssl', label: 'SSL', type: 'select', icon: <FileText className="h-4 w-4" /> }
    ],
    'Snowflake': [
      { name: 'account', label: 'Account', type: 'text', icon: <Server className="h-4 w-4" /> },
      { name: 'user', label: 'User', type: 'text', icon: <User className="h-4 w-4" /> },
      { name: 'password', label: 'Password', type: 'password', icon: <Key className="h-4 w-4" /> },
      { name: 'role', label: 'Role (Optional)', type: 'text', icon: <FileText className="h-4 w-4" /> },
      { name: 'warehouse', label: 'Warehouse', type: 'text', icon: <Database className="h-4 w-4" /> },
      { name: 'database', label: 'Database', type: 'text', icon: <Database className="h-4 w-4" /> },
      { name: 'schema', label: 'Schema', type: 'text', icon: <FileText className="h-4 w-4" /> }
    ],
    'Databricks': [
      { name: 'server_hostname', label: 'Server Hostname', type: 'text', icon: <Server className="h-4 w-4" /> },
      { name: 'http_path', label: 'HTTP Path', type: 'text', icon: <FileText className="h-4 w-4" /> },
      { name: 'access_token', label: 'Access Token', type: 'password', icon: <Key className="h-4 w-4" /> },
      { name: 'catalog', label: 'Catalog (Optional)', type: 'text', icon: <Database className="h-4 w-4" /> },
      { name: 'schema', label: 'Schema (Optional)', type: 'text', icon: <FileText className="h-4 w-4" /> }
    ],
    'Oracle': [
      { name: 'host', label: 'Host', type: 'text', icon: <Server className="h-4 w-4" /> },
      { name: 'port', label: 'Port', type: 'number', icon: <Hash className="h-4 w-4" /> },
      { name: 'service_name', label: 'Service Name', type: 'text', icon: <Database className="h-4 w-4" /> },
      { name: 'username', label: 'Username', type: 'text', icon: <User className="h-4 w-4" /> },
      { name: 'password', label: 'Password', type: 'password', icon: <Key className="h-4 w-4" /> }
    ],
    'SQL Server': [
      { name: 'host', label: 'Host', type: 'text', icon: <Server className="h-4 w-4" /> },
      { name: 'port', label: 'Port', type: 'number', icon: <Hash className="h-4 w-4" /> },
      { name: 'database', label: 'Database', type: 'text', icon: <Database className="h-4 w-4" /> },
      { name: 'username', label: 'Username', type: 'text', icon: <User className="h-4 w-4" /> },
      { name: 'password', label: 'Password', type: 'password', icon: <Key className="h-4 w-4" /> },
      { name: 'driver', label: 'Driver', type: 'text', icon: <FileText className="h-4 w-4" /> }
    ],
    'Teradata': [
      { name: 'host', label: 'Host', type: 'text', icon: <Server className="h-4 w-4" /> },
      { name: 'username', label: 'Username', type: 'text', icon: <User className="h-4 w-4" /> },
      { name: 'password', label: 'Password', type: 'password', icon: <Key className="h-4 w-4" /> },
      { name: 'database', label: 'Database (Optional)', type: 'text', icon: <Database className="h-4 w-4" /> }
    ],
    'Google BigQuery': [
      { name: 'project_id', label: 'Project ID', type: 'text', icon: <Server className="h-4 w-4" /> },
      { name: 'dataset', label: 'Dataset (Optional)', type: 'text', icon: <Database className="h-4 w-4" /> },
      { name: 'credentials_json', label: 'Credentials JSON', type: 'textarea', icon: <FileText className="h-4 w-4" /> }
    ]
  };

  const handleCredentialChange = (field: string, value: string) => {
    setCredentials(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    
    try {
      const response = await fetch('/api/connections/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          dbType: databaseType,
          name: connectionName,
          credentials
        })
      });
      
      const result = await response.json();
      setTestResult(result);
    } catch (error) {
      setTestResult({
        ok: false,
        message: 'Failed to test connection'
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSaveConnection = async () => {
    if (!testResult?.ok) return;
    
    setIsSaving(true);
    
    try {
      const endpoint = editingConnection 
        ? `/api/connections/${editingConnection.id}` 
        : '/api/connections/save';
      
      const method = editingConnection ? 'PUT' : 'POST';
      
      const response = await fetch(endpoint, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          dbType: databaseType,
          name: connectionName,
          credentials
        })
      });
      
      const result = await response.json();
      if (result.ok) {
        onConnectionSaved();
        onClose();
      }
    } catch (error) {
      console.error('Failed to save connection:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-[#085690]">
              {editingConnection ? 'Edit Database Connection' : 'Add Database Connection'}
            </h2>
            <button 
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[#085690] mb-1">
                Connection Name
              </label>
              <div className="relative">
                <Database className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  value={connectionName}
                  onChange={(e) => setConnectionName(e.target.value)}
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#085690] focus:border-transparent"
                  placeholder="Enter connection name"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-[#085690] mb-1">
                Database Type
              </label>
              <select
                value={databaseType}
                onChange={(e) => setDatabaseType(e.target.value as DatabaseType)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#085690] focus:border-transparent"
              >
                {databaseTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-[#085690] mb-3">Credentials</h3>
              <div className="space-y-3">
                {credentialFields[databaseType].map((field) => (
                  <div key={field.name}>
                    <label className="block text-sm font-medium text-[#085690] mb-1">
                      {field.label}
                    </label>
                    {field.type === 'select' ? (
                      <select
                        value={credentials[field.name] || ''}
                        onChange={(e) => handleCredentialChange(field.name, e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#085690] focus:border-transparent"
                      >
                        {field.name === 'ssl' ? (
                          <>
                            <option value="true">Enabled</option>
                            <option value="false">Disabled</option>
                          </>
                        ) : (
                          <>
                            <option value="require">require</option>
                            <option value="prefer">prefer</option>
                            <option value="disable">disable</option>
                          </>
                        )}
                      </select>
                    ) : field.type === 'textarea' ? (
                      <textarea
                        value={credentials[field.name] || ''}
                        onChange={(e) => handleCredentialChange(field.name, e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#085690] focus:border-transparent"
                        rows={4}
                        placeholder={`Enter ${field.label.toLowerCase()}`}
                      />
                    ) : (
                      <div className="relative">
                        {field.icon && (
                          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                            {field.icon}
                          </div>
                        )}
                        <input
                          type={field.type}
                          value={credentials[field.name] || ''}
                          onChange={(e) => handleCredentialChange(field.name, e.target.value)}
                          className={`w-full ${field.icon ? 'pl-10' : 'pl-3'} pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#085690] focus:border-transparent`}
                          placeholder={`Enter ${field.label.toLowerCase()}`}
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
            
            <div className="flex items-center space-x-4 pt-4">
              <button
                onClick={handleTestConnection}
                disabled={isTesting || !connectionName}
                className={`px-4 py-2 rounded-md ${
                  isTesting 
                    ? 'bg-gray-300 text-gray-500' 
                    : 'bg-[#085690] text-white hover:bg-[#064a7a]'
                } disabled:opacity-50 flex items-center`}
              >
                {isTesting ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Testing...
                  </>
                ) : (
                  'Test Connection'
                )}
              </button>
              
              {testResult && (
                <div className={`flex items-center ${testResult.ok ? 'text-green-600' : 'text-red-600'}`}>
                  {testResult.ok ? (
                    <CheckCircle className="h-5 w-5 mr-1" />
                  ) : (
                    <AlertCircle className="h-5 w-5 mr-1" />
                  )}
                  <span className="text-sm">{testResult.message || (testResult.ok ? 'Connection successful!' : 'Connection failed')}</span>
                </div>
              )}
            </div>
            
            <div className="flex justify-end space-x-3 pt-4 border-t">
              <button
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveConnection}
                disabled={isSaving || !testResult?.ok}
                className={`px-4 py-2 rounded-md ${
                  isSaving 
                    ? 'bg-gray-300 text-gray-500' 
                    : 'bg-[#ec6225] text-white hover:bg-[#d4551e]'
                } disabled:opacity-50 flex items-center`}
              >
                {isSaving ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Saving...
                  </>
                ) : (
                  editingConnection ? 'Update Connection' : 'Save Connection'
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AddConnectionModal;