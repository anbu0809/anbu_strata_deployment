import { useState, useEffect } from 'react';
import { Connection, Session, AnalysisStatus } from '../types';
import { Play, CheckCircle, AlertCircle, FileText, FileSpreadsheet, File, ChevronDown, ChevronRight, RefreshCw } from 'lucide-react';

interface AnalyzeProps {
  connections: Connection[];
}

const Analyze = ({ connections }: AnalyzeProps) => {
  const [session, setSession] = useState<Session>({ source: null, target: null });
  const [sourceId, setSourceId] = useState<number | ''>('');
  const [targetId, setTargetId] = useState<number | ''>('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus | null>(null);
  const [canProceed, setCanProceed] = useState(false);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    tables: false,
    views: false,
    procedures: false,
    functions: false,
    triggers: false,
    indexes: false
  });
  const [pollingInterval, setPollingInterval] = useState<any>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // Fetch current session on component mount
  useEffect(() => {
    fetchSession();
    // Don't check for existing analysis status at all
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, []);

  const startPolling = () => {
    if (!pollingInterval) {
      const interval = setInterval(fetchAnalysisStatus, 2000);
      setPollingInterval(interval);
    }
  };

  const stopPolling = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
  };

  const fetchSession = async () => {
    try {
      const response = await fetch('/api/session');
      if (response.ok) {
        const data = await response.json();
        setSession(data);
        if (data.source) setSourceId(data.source.id);
        if (data.target) setTargetId(data.target.id);
      }
    } catch (error) {
      console.error('Failed to fetch session:', error);
    }
  };

  const fetchAnalysisStatus = async () => {
    try {
      const response = await fetch('/api/analyze/status');
      if (response.ok) {
        const data = await response.json();
        setAnalysisStatus(data);
        if (data.done) {
          setIsAnalyzing(false);
          setCanProceed(true);
          stopPolling();
          // Fetch analysis data for display
          fetchAnalysisData();
        }
      }
    } catch (error) {
      console.error('Failed to fetch analysis status:', error);
    }
  };

  const fetchAnalysisData = async () => {
    try {
      const response = await fetch('/api/analyze/data');
      if (response.ok) {
        const data = await response.json();
        setAnalysisData(data);
        setLastRefresh(new Date());
      }
    } catch (error) {
      console.error('Failed to fetch analysis data:', error);
    }
  };

  const handleRefreshAnalysis = async () => {
    if (sourceId && targetId) {
      try {
        // Clear existing analysis data first
        setAnalysisData(null);
        
        // Start a fresh analysis
        setIsAnalyzing(true);
        setAnalysisStatus(null);
        setCanProceed(false);
        
        const response = await fetch('/api/analyze/start', {
          method: 'POST',
        });
        
        if (response.ok) {
          startPolling();
        }
      } catch (error) {
        console.error('Failed to refresh analysis:', error);
        setIsAnalyzing(false);
      }
    } else {
      // Just refresh the data without starting analysis
      await fetchAnalysisData();
    }
  };

  const formatLastRefresh = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const handleSourceChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newSourceId = Number(e.target.value);
    setSourceId(newSourceId);
    // Do nothing else - no automatic session setting
  };

  const handleTargetChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newTargetId = Number(e.target.value);
    setTargetId(newTargetId);
    // Do nothing else - no automatic session setting
  };

  const handleStartAnalysis = async () => {
    // Only when user clicks this button:
    if (sourceId && targetId) {
      try {
        // 1. First set the session
        const sessionResponse = await fetch('/api/session/set-source-target', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            sourceId,
            targetId
          })
        });
        
        if (sessionResponse.ok) {
          await fetchSession();
          
          // 2. Then start the analysis
          setIsAnalyzing(true);
          setAnalysisStatus(null);
          setCanProceed(false);
          setAnalysisData(null);
          
          const response = await fetch('/api/analyze/start', {
            method: 'POST',
          });
          
          if (response.ok) {
            // 3. Start polling for status
            startPolling();
          }
        }
      } catch (error) {
        console.error('Failed to start analysis:', error);
        setIsAnalyzing(false);
      }
    }
  };

  const handleExport = async (format: 'pdf' | 'json' | 'xlsx') => {
    try {
      const response = await fetch(`/api/analyze/export/${format}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analysis_report.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error(`Failed to export ${format}:`, error);
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const renderDatabaseInfo = () => {
    if (!analysisData) return null;
    
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-[#085690] p-4 rounded-lg">
          <p className="text-sm text-white font-medium">Database Type</p>
          <p className="text-lg font-semibold text-white">{analysisData.database_type}</p>
        </div>
        <div className="bg-[#085690] p-4 rounded-lg">
          <p className="text-sm text-white font-medium">Version</p>
          <p className="text-lg font-semibold text-white">{analysisData.version}</p>
        </div>
        <div className="bg-[#085690] p-4 rounded-lg">
          <p className="text-sm text-white font-medium">Charset</p>
          <p className="text-lg font-semibold text-white">{analysisData.charset}</p>
        </div>
        <div className="bg-[#085690] p-4 rounded-lg">
          <p className="text-sm text-white font-medium">Collation</p>
          <p className="text-lg font-semibold text-white">{analysisData.collation}</p>
        </div>
      </div>
    );
  };

  const renderTablesSection = () => {
    if (!analysisData?.tables || analysisData.tables.length === 0) return null;
    
    return (
      <div className="mb-6">
        <div 
          className="flex items-center justify-between cursor-pointer p-3 bg-[#085690] rounded-lg"
          onClick={() => toggleSection('tables')}
        >
          <h3 className="text-lg font-medium text-white">Tables ({analysisData.tables.length})</h3>
          {expandedSections.tables ? <ChevronDown className="h-5 w-5 text-white" /> : <ChevronRight className="h-5 w-5 text-white" />}
        </div>
        
        {expandedSections.tables && (
          <div className="mt-2 border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Table Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Engine</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rows</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data Size</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {analysisData.tables.map((table: any, index: number) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{table.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{table.type}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{table.engine}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{table.estimated_rows?.toLocaleString()}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{table.data_length ? `${(table.data_length / 1024 / 1024).toFixed(2)} MB` : '0 MB'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderViewsSection = () => {
    if (!analysisData?.views || analysisData.views.length === 0) return null;
    
    return (
      <div className="mb-6">
        <div 
          className="flex items-center justify-between cursor-pointer p-3 bg-gray-50 rounded-lg"
          onClick={() => toggleSection('views')}
        >
          <h3 className="text-lg font-medium text-gray-900">Views ({analysisData.views.length})</h3>
          {expandedSections.views ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
        </div>
        
        {expandedSections.views && (
          <div className="mt-2 border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">View Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Definition</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {analysisData.views.map((view: any, index: number) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{view.name}</td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        <pre className="text-xs overflow-x-auto max-w-md">{view.definition?.substring(0, 100)}{view.definition?.length > 100 ? '...' : ''}</pre>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderProceduresSection = () => {
    if (!analysisData?.procedures || analysisData.procedures.length === 0) return null;
    
    return (
      <div className="mb-6">
        <div 
          className="flex items-center justify-between cursor-pointer p-3 bg-gray-50 rounded-lg"
          onClick={() => toggleSection('procedures')}
        >
          <h3 className="text-lg font-medium text-gray-900">Stored Procedures ({analysisData.procedures.length})</h3>
          {expandedSections.procedures ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
        </div>
        
        {expandedSections.procedures && (
          <div className="mt-2 border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Procedure Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Definition</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {analysisData.procedures.map((proc: any, index: number) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{proc.name}</td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        <pre className="text-xs overflow-x-auto max-w-md">{proc.definition?.substring(0, 100)}{proc.definition?.length > 100 ? '...' : ''}</pre>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Analyze</h1>
        <div className="flex items-center justify-between">
          <p className="text-gray-600">Select source and target databases for analysis</p>
          <button
            onClick={handleRefreshAnalysis}
            className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-[#ec6225] border border-gray-300 rounded-md hover:border-[#ec6225]"
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh Data
          </button>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Source Database
            </label>
            <div className="flex space-x-2">
              <select
                value={sourceId}
                onChange={handleSourceChange}
                className="flex-1 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
              >
                <option value="">Select source database</option>
                {connections.map(conn => (
                  <option key={conn.id} value={conn.id}>
                    {conn.name} ({conn.dbType})
                  </option>
                ))}
              </select>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Database
            </label>
            <div className="flex space-x-2">
              <select
                value={targetId}
                onChange={handleTargetChange}
                className="flex-1 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
              >
                <option value="">Select target database</option>
                {connections.map(conn => (
                  <option key={conn.id} value={conn.id}>
                    {conn.name} ({conn.dbType})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
        
        {sourceId && targetId && (
          <div className="mt-6 p-4 bg-blue-50 rounded-md">
            <div className="flex items-center">
              <div>
                <p className="font-medium text-blue-800">
                  Source: {connections.find(c => c.id === sourceId)?.name} ({connections.find(c => c.id === sourceId)?.dbType})
                </p>
                <p className="font-medium text-blue-800">
                  Target: {connections.find(c => c.id === targetId)?.name} ({connections.find(c => c.id === targetId)?.dbType})
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {(isAnalyzing || (analysisStatus && (analysisStatus.percent !== null && analysisStatus.percent > 0 || analysisStatus.done))) ? (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Analysis Progress</h2>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">
                Last updated: {formatLastRefresh(lastRefresh)}
              </span>
              <button
                onClick={handleRefreshAnalysis}
                disabled={isAnalyzing}
                className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-[#ec6225] border border-gray-300 rounded-md hover:border-[#ec6225] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className={`h-4 w-4 mr-1 ${isAnalyzing ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>
          
          {analysisStatus && (
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700">
                    {analysisStatus.phase || 'Initializing...'}
                  </span>
                  <span className="text-sm font-medium text-gray-700">
                    {analysisStatus.percent || 0}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
                    style={{ width: `${analysisStatus.percent || 0}%` }}
                  ></div>
                </div>
              </div>
              
              {analysisStatus.done && (
                <div className="p-4 bg-green-50 rounded-md border border-green-200">
                  <div className="flex items-center">
                    <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                    <span className="font-medium text-green-800">AI analysis completed</span>
                  </div>
                  
                  {/* Display analysis results */}
                  {analysisData && (
                    <div className="mt-4">
                      {renderDatabaseInfo()}
                      {renderTablesSection()}
                      {renderViewsSection()}
                      {renderProceduresSection()}
                      
                      {/* Export buttons */}
                      <div className="mt-6 pt-4 border-t border-gray-200">
                        <h3 className="text-lg font-medium text-gray-900 mb-3">Export Report</h3>
                        <div className="flex flex-wrap gap-2">
                          <button
                            onClick={() => handleExport('pdf')}
                            className="flex items-center px-3 py-2 text-gray-700 hover:text-[#ec6225] border border-gray-300 rounded-md hover:border-[#ec6225]"
                          >
                            <File className="h-4 w-4 mr-2" />
                            Download PDF
                          </button>
                          <button
                            onClick={() => handleExport('xlsx')}
                            className="flex items-center px-3 py-2 text-gray-700 hover:text-[#ec6225] border border-gray-300 rounded-md hover:border-[#ec6225]"
                          >
                            <FileSpreadsheet className="h-4 w-4 mr-2" />
                            Download Excel
                          </button>
                          <button
                            onClick={() => handleExport('json')}
                            className="flex items-center px-3 py-2 text-gray-700 hover:text-[#ec6225] border border-gray-300 rounded-md hover:border-[#ec6225]"
                          >
                            <FileText className="h-4 w-4 mr-2" />
                            Download JSON
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              {analysisStatus.resultsSummary && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  {Object.entries(analysisStatus.resultsSummary).map(([key, value]) => (
                    <div key={key} className="p-3 bg-gray-50 rounded-md">
                      <p className="text-sm text-gray-600 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</p>
                      <p className="text-lg font-semibold">{value as string}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Analysis Started</h3>
          <p className="text-gray-500 mb-4">
            Select source and target databases, then click "Start Analysis" to begin.
          </p>
          <div className="flex justify-center items-center space-x-4">
            <button
              onClick={handleRefreshAnalysis}
              className="flex items-center px-4 py-2 text-gray-600 hover:text-[#ec6225] border border-gray-300 rounded-md hover:border-[#ec6225]"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Check for Analysis Data
            </button>
            <span className="text-sm text-gray-500">
              Last checked: {formatLastRefresh(lastRefresh)}
            </span>
          </div>
        </div>
      )}
      
      {/* Start Analysis and Proceed to Extraction buttons at the end of the page */}
      <div className="mt-6 flex justify-center space-x-4">
        {!isAnalyzing && !analysisStatus?.done && sourceId && targetId && (
          <button
            onClick={handleStartAnalysis}
            className="px-6 py-3 bg-[#ec6225] text-white rounded-md hover:bg-[#d4551e] flex items-center text-lg"
          >
            <Play className="h-5 w-5 mr-2" />
            Start Analysis
          </button>
        )}
        {canProceed && (
          <button
            onClick={() => window.location.href = '/extract'}
            className="px-6 py-3 bg-[#085690] text-white rounded-md hover:bg-[#064a7a] flex items-center text-lg"
          >
            <CheckCircle className="h-5 w-5 mr-2" />
            Proceed to Extraction
          </button>
        )}
      </div>

      {/* Footer */}
      <div className="mt-12 text-center">
        <p className="text-lg font-bold text-gray-900 mb-2">DecisionMinds</p>
        <p className="text-sm text-gray-600">Powered by DecisionMinds</p>
      </div>
    </div>
  );
};

export default Analyze;