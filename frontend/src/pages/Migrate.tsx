import { useState, useEffect } from 'react';
import { Play, CheckCircle, AlertCircle, Database, Table, ChevronDown, ChevronRight } from 'lucide-react';

const Migrate = () => {
  const [session, setSession] = useState<any>(null);
  const [structureStatus, setStructureStatus] = useState<any>(null);
  const [dataStatus, setDataStatus] = useState<any>(null);
  const [canMigrateData, setCanMigrateData] = useState(false);
  const [canProceed, setCanProceed] = useState(false);
  const [translatedQueries, setTranslatedQueries] = useState<string>("");
  const [migrationNotes, setMigrationNotes] = useState<string>("");
  const [showQueries, setShowQueries] = useState(false);
  const [structureMigrationStarted, setStructureMigrationStarted] = useState(false);
  const [dataMigrationStarted, setDataMigrationStarted] = useState(false);

  // Fetch current session on component mount
  useEffect(() => {
    fetchSession();
  }, []);

  // Poll for status only when migrations are active
  useEffect(() => {
    let interval: any = null;
    
    if (structureMigrationStarted || dataMigrationStarted) {
      interval = setInterval(fetchMigrationStatus, 2000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [structureMigrationStarted, dataMigrationStarted]);

  const fetchSession = async () => {
    try {
      const response = await fetch('/api/session');
      if (response.ok) {
        const data = await response.json();
        setSession(data);
      }
    } catch (error) {
      console.error('Failed to fetch session:', error);
    }
  };

  const fetchMigrationStatus = async () => {
    try {
      // Fetch structure migration status ONLY if we've started it
      if (structureMigrationStarted) {
        const structureResponse = await fetch('/api/migrate/structure/status');
        if (structureResponse.ok) {
          const structureData = await structureResponse.json();
          setStructureStatus(structureData);
          // Enable data migration button only after structure migration is done
          if (structureData.done) {
            setCanMigrateData(true);
            // Stop polling for structure status
            setStructureMigrationStarted(false);
            // Fetch translated queries when structure migration is done
            fetchTranslatedQueries();
          }
        }
      }
      
      // Fetch data migration status ONLY if we've started it
      if (dataMigrationStarted) {
        const dataResponse = await fetch('/api/migrate/data/status');
        if (dataResponse.ok) {
          const dataData = await dataResponse.json();
          setDataStatus(dataData);
          if (dataData.done) {
            setCanProceed(true);
            // Stop polling for data status
            setDataMigrationStarted(false);
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch migration status:', error);
    }
  };

  const fetchTranslatedQueries = async () => {
    try {
      const response = await fetch('/api/migrate/structure/queries');
      if (response.ok) {
        const data = await response.json();
        setTranslatedQueries(data.translated_queries || "");
        setMigrationNotes(data.notes || "");
      }
    } catch (error) {
      console.error('Failed to fetch translated queries:', error);
    }
  };

  const handleMigrateStructure = async () => {
    // Reset states when starting structure migration
    setStructureStatus(null);
    setDataStatus(null);
    setCanMigrateData(false);
    setCanProceed(false);
    setStructureMigrationStarted(true);
    setDataMigrationStarted(false);
    
    try {
      const response = await fetch('/api/migrate/structure', {
        method: 'POST',
      });
      
      if (response.ok) {
        // Status will be polled through the useEffect hook
      }
    } catch (error) {
      console.error('Failed to start structure migration:', error);
      setStructureMigrationStarted(false);
    }
  };

  const handleMigrateData = async () => {
    // Only allow data migration if structure migration is complete
    if (!structureStatus || !structureStatus.done) {
      return;
    }
    
    // Reset data migration status and start polling
    setDataStatus(null);
    setDataMigrationStarted(true);
    
    try {
      const response = await fetch('/api/migrate/data', {
        method: 'POST',
      });
      
      if (response.ok) {
        // Status will be polled through the useEffect hook
      }
    } catch (error) {
      console.error('Failed to start data migration:', error);
      setDataMigrationStarted(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#085690] mb-2">Migrate</h1>
        <p className="text-gray-600">Migrate database structure and data</p>
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold text-[#085690] mb-4">Database Summary</h2>
        
        {session ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="border rounded-lg p-4">
              <div className="flex items-center mb-3">
                <Database className="h-5 w-5 text-[#085690] mr-2" />
                <h3 className="font-medium text-[#085690]">Source Database</h3>
              </div>
              {session.source ? (
                <>
                  <p className="text-gray-700">{session.source.name}</p>
                  <p className="text-sm text-gray-500">{session.source.dbType}</p>
                </>
              ) : (
                <p className="text-gray-500">No source database selected</p>
              )}
            </div>
            
            <div className="border rounded-lg p-4">
              <div className="flex items-center mb-3">
                <Database className="h-5 w-5 text-[#085690] mr-2" />
                <h3 className="font-medium text-[#085690]">Target Database</h3>
              </div>
              {session.target ? (
                <>
                  <p className="text-gray-700">{session.target.name}</p>
                  <p className="text-sm text-gray-500">{session.target.dbType}</p>
                </>
              ) : (
                <p className="text-gray-500">No target database selected</p>
              )}
            </div>
          </div>
        ) : (
          <p className="text-gray-500">Loading session data...</p>
        )}
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Structure Migration */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-[#085690] mb-4 flex items-center">
            <Database className="h-5 w-5 mr-2 text-[#085690]" />
            Migrate Structure
          </h2>
          
          {structureStatus ? (
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700">
                    {structureStatus.phase || 'Initializing...'}
                  </span>
                  <span className="text-sm font-medium text-gray-700">
                    {structureStatus.percent || 0}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
                    style={{ width: `${structureStatus.percent || 0}%` }}
                  ></div>
                </div>
              </div>
              
              {structureStatus.done && (
                <div className="space-y-4">
                  <div className="p-3 bg-green-50 rounded-md border border-green-200">
                    <div className="flex items-center">
                      <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                      <span className="font-medium text-green-800">Structure migration completed</span>
                    </div>
                  </div>
                  
                  {/* Display AI-generated queries */}
                  <div className="border rounded-lg">
                    <div 
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-t-lg cursor-pointer"
                      onClick={() => setShowQueries(!showQueries)}
                    >
                      <h3 className="font-medium text-gray-900">AI-Generated Queries</h3>
                      {showQueries ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
                    </div>
                    
                    {showQueries && (
                      <div className="p-3">
                        {migrationNotes && (
                          <div className="mb-4 p-3 bg-yellow-50 rounded-md border border-yellow-200">
                            <h4 className="font-medium text-yellow-800 mb-2">Notes:</h4>
                            <p className="text-sm text-yellow-700">{migrationNotes}</p>
                          </div>
                        )}
                        
                        {translatedQueries ? (
                          <div className="bg-gray-50 p-3 rounded-md">
                            <pre className="text-sm overflow-x-auto max-h-60 whitespace-pre-wrap">
                              {translatedQueries}
                            </pre>
                          </div>
                        ) : (
                          <p className="text-gray-500">No queries generated</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {structureStatus.error && (
                <div className="p-3 bg-red-50 rounded-md border border-red-200">
                  <div className="flex items-center">
                    <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
                    <span className="font-medium text-red-800">Error: {structureStatus.error}</span>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <button
                onClick={handleMigrateStructure}
                className="px-4 py-2 bg-[#ec6225] text-white rounded-md hover:bg-[#d4551e] flex items-center mx-auto"
              >
                <Play className="h-4 w-4 mr-2" />
                Migrate Structure
              </button>
            </div>
          )}
        </div>
        
        {/* Data Migration */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <Table className="h-5 w-5 mr-2 text-indigo-600" />
            Migrate Data
          </h2>
          
          {dataStatus ? (
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700">
                    {dataStatus.phase || 'Initializing...'}
                  </span>
                  <span className="text-sm font-medium text-gray-700">
                    {dataStatus.percent || 0}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
                    style={{ width: `${dataStatus.percent || 0}%` }}
                  ></div>
                </div>
                
                {/* Data migration progress */}
                {dataStatus.rows_migrated !== undefined && dataStatus.total_rows !== undefined && (
                  <div className="mt-2 text-sm text-gray-600">
                    Migrated {dataStatus.rows_migrated?.toLocaleString()} of {dataStatus.total_rows?.toLocaleString()} rows
                  </div>
                )}
              </div>
              
              {dataStatus.done && (
                <div className="p-3 bg-green-50 rounded-md border border-green-200">
                  <div className="flex items-center">
                    <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                    <span className="font-medium text-green-800">Data migration completed</span>
                  </div>
                </div>
              )}
              
              {dataStatus.error && (
                <div className="p-3 bg-red-50 rounded-md border border-red-200">
                  <div className="flex items-center">
                    <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
                    <span className="font-medium text-red-800">Error: {dataStatus.error}</span>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <button
                onClick={handleMigrateData}
                disabled={!canMigrateData}
                className={`px-4 py-2 rounded-md flex items-center mx-auto ${
                  canMigrateData
                    ? 'bg-[#ec6225] text-white hover:bg-[#d4551e]'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                <Play className="h-4 w-4 mr-2" />
                Migrate Data
              </button>
              {!canMigrateData && (
                <p className="text-sm text-gray-500 mt-2">
                  Complete structure migration first
                </p>
              )}
            </div>
          )}
        </div>
      </div>
      
      {canProceed && (
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Migration Complete</h2>
              <p className="text-gray-600">Structure and data have been successfully migrated</p>
            </div>
            <button
              onClick={() => window.location.href = '/reconcile'}
              className="px-4 py-2 bg-[#085690] text-white rounded-md hover:bg-[#064a7a] flex items-center"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Proceed to Validation
            </button>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-12 text-center">
        <img
          src="/src/assets/dm_logo.png"
          alt="DecisionMinds"
          className="h-8 w-auto mx-auto"
        />
        <p className="text-sm text-gray-600 mt-2">Powered by DecisionMinds</p>
      </div>
    </div>
  );
};

export default Migrate;