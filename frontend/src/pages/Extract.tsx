import { useState, useEffect } from 'react';
import { Play, CheckCircle, AlertCircle, Database, FileText, FileSpreadsheet, File, ChevronDown, ChevronRight } from 'lucide-react';

const Extract = () => {
  const [session, setSession] = useState<any>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionStatus, setExtractionStatus] = useState<any>(null);
  const [canProceed, setCanProceed] = useState(false);
  const [extractionData, setExtractionData] = useState<any>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    tables: false,
    views: false,
    procedures: false,
    functions: false,
    triggers: false,
    indexes: false,
    constraints: false
  });

  // Fetch current session on component mount and cleanup on unmount
  useEffect(() => {
    fetchSession();
    
    return () => {
      // Cleanup polling interval on component unmount
      if ((window as any).extractionPollInterval) {
        clearInterval((window as any).extractionPollInterval);
        (window as any).extractionPollInterval = null;
      }
    };
  }, []);

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

  const fetchExtractionStatus = async () => {
    try {
      const response = await fetch('/api/extract/status');
      if (response.ok) {
        const data = await response.json();
        setExtractionStatus(data);
        if (data.done) {
          setIsExtracting(false);
          setCanProceed(true);
          // Stop polling when extraction is complete
          if ((window as any).extractionPollInterval) {
            clearInterval((window as any).extractionPollInterval);
            (window as any).extractionPollInterval = null;
          }
          // Fetch extraction data for display
          fetchExtractionData();
        }
      }
    } catch (error) {
      console.error('Failed to fetch extraction status:', error);
      // Stop polling on error
      if ((window as any).extractionPollInterval) {
        clearInterval((window as any).extractionPollInterval);
        (window as any).extractionPollInterval = null;
      }
      setIsExtracting(false);
    }
  };

  const fetchExtractionData = async () => {
    try {
      const response = await fetch('/api/extract/data');
      if (response.ok) {
        const data = await response.json();
        setExtractionData(data);
      }
    } catch (error) {
      console.error('Failed to fetch extraction data:', error);
    }
  };

  const handleStartExtraction = async () => {
    setIsExtracting(true);
    setExtractionStatus(null);
    setCanProceed(false);
    setExtractionData(null);
    
    try {
      const response = await fetch('/api/extract/start', {
        method: 'POST',
      });
      
      if (response.ok) {
        // Start polling for status only after button click
        const interval = setInterval(fetchExtractionStatus, 2000);
        // Store interval ID for cleanup
        (window as any).extractionPollInterval = interval;
      }
    } catch (error) {
      console.error('Failed to start extraction:', error);
      setIsExtracting(false);
    }
  };

  const handleExport = async (format: 'pdf' | 'json' | 'xlsx') => {
    try {
      const response = await fetch(`/api/extract/export/${format}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `extraction_report.${format}`;
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

  const renderSummary = () => {
    if (!extractionData?.extraction_report) return null;
    
    const report = extractionData.extraction_report;
    const summaryItems = [
      { label: 'Tables', value: report.tables, color: '[#085690]' },
      { label: 'Views', value: report.views, color: '[#085690]' },
      { label: 'Procedures', value: report.procedures, color: '[#085690]' },
      { label: 'Functions', value: report.functions, color: '[#085690]' },
      { label: 'Triggers', value: report.triggers, color: '[#ec6225]' },
      { label: 'Indexes', value: report.indexes, color: '[#085690]' },
      { label: 'Constraints', value: report.constraints, color: '[#085690]' },
      { label: 'Sequences', value: report.sequences, color: '[#085690]' }
    ];
    
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {summaryItems.map((item, index) => (
          <div key={index} className={`bg-${item.color} p-4 rounded-lg`}>
            <p className="text-sm text-white font-medium">{item.label}</p>
            <p className="text-lg font-semibold text-white">{item.value}</p>
          </div>
        ))}
      </div>
    );
  };

  const renderTablesSection = () => {
    if (!extractionData?.ddl_scripts?.tables || extractionData.ddl_scripts.tables.length === 0) return null;
    
    return (
      <div className="mb-6">
        <div 
          className="flex items-center justify-between cursor-pointer p-3 bg-[#085690] rounded-lg"
          onClick={() => toggleSection('tables')}
        >
          <h3 className="text-lg font-medium text-white">Tables ({extractionData.ddl_scripts.tables.length})</h3>
          {expandedSections.tables ? <ChevronDown className="h-5 w-5 text-white" /> : <ChevronRight className="h-5 w-5 text-white" />}
        </div>
        
        {expandedSections.tables && (
          <div className="mt-2 border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[#085690] uppercase tracking-wider">Table Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[#085690] uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[#085690] uppercase tracking-wider">DDL Preview</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {extractionData.ddl_scripts.tables.map((table: any, index: number) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{table.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{table.type}</td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        <pre className="text-xs overflow-x-auto max-w-md">{table.ddl?.substring(0, 100)}{table.ddl?.length > 100 ? '...' : ''}</pre>
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

  const renderTriggersSection = () => {
    if (!extractionData?.ddl_scripts?.triggers || extractionData.ddl_scripts.triggers.length === 0) return null;
    
    return (
      <div className="mb-6">
        <div 
          className="flex items-center justify-between cursor-pointer p-3 bg-[#ec6225] rounded-lg"
          onClick={() => toggleSection('triggers')}
        >
          <h3 className="text-lg font-medium text-white">Triggers ({extractionData.ddl_scripts.triggers.length})</h3>
          {expandedSections.triggers ? <ChevronDown className="h-5 w-5 text-white" /> : <ChevronRight className="h-5 w-5 text-white" />}
        </div>
        
        {expandedSections.triggers && (
          <div className="mt-2 border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trigger Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Table</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Event</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timing</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {extractionData.ddl_scripts.triggers.map((trigger: any, index: number) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{trigger.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{trigger.table}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{trigger.event}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{trigger.timing}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
  
        {/* Footer */}
        <div className="mt-12 text-center">
          <p className="text-lg font-bold text-gray-900 mb-2">DecisionMinds</p>
          <p className="text-sm text-gray-600">Powered by DecisionMinds</p>
        </div>
      </div>
    );
  };

  const renderConstraintsSection = () => {
    if (!extractionData?.constraints || extractionData.constraints.length === 0) return null;
    
    return (
      <div className="mb-6">
        <div 
          className="flex items-center justify-between cursor-pointer p-3 bg-gray-50 rounded-lg"
          onClick={() => toggleSection('constraints')}
        >
          <h3 className="text-lg font-medium text-gray-900">Constraints ({extractionData.constraints.length})</h3>
          {expandedSections.constraints ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
        </div>
        
        {expandedSections.constraints && (
          <div className="mt-2 border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Table</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Columns</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {extractionData.constraints.map((constraint: any, index: number) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{constraint.type}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{constraint.table}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{constraint.columns?.join(', ')}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{constraint.name}</td>
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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Extract</h1>
        <p className="text-gray-600">Extract database schema and objects</p>
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Database Summary</h2>
        
        {session ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="border rounded-lg p-4">
              <div className="flex items-center mb-3">
                <Database className="h-5 w-5 text-indigo-600 mr-2" />
                <h3 className="font-medium text-gray-900">Source Database</h3>
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
                <Database className="h-5 w-5 text-indigo-600 mr-2" />
                <h3 className="font-medium text-gray-900">Target Database</h3>
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
        
        <div className="mt-6">
          {!isExtracting && !extractionStatus?.done && (
            <button
              onClick={handleStartExtraction}
              className="px-4 py-2 bg-[#ec6225] text-white rounded-md hover:bg-[#d4551e] flex items-center"
            >
              <Play className="h-4 w-4 mr-2" />
              Run Extraction
            </button>
          )}
          
          {canProceed && (
            <button
              onClick={() => window.location.href = '/migrate'}
              className="px-4 py-2 bg-[#085690] text-white rounded-md hover:bg-[#064a7a] flex items-center mt-4"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Proceed to Migration
            </button>
          )}
        </div>
      </div>
      
      {isExtracting || extractionStatus ? (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Extraction Progress</h2>
          
          {extractionStatus && (
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700">
                    {extractionStatus.phase || 'Initializing...'}
                  </span>
                  <span className="text-sm font-medium text-gray-700">
                    {extractionStatus.percent || 0}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
                    style={{ width: `${extractionStatus.percent || 0}%` }}
                  ></div>
                </div>
              </div>
              
              {extractionStatus.done && (
                <div className="p-4 bg-green-50 rounded-md border border-green-200">
                  <div className="flex items-center">
                    <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                    <span className="font-medium text-green-800">Extraction completed successfully</span>
                  </div>
                  
                  {/* Display extraction results */}
                  {extractionData && (
                    <div className="mt-4">
                      {renderSummary()}
                      {renderTablesSection()}
                      {renderTriggersSection()}
                      {renderConstraintsSection()}
                      
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
              
              {extractionStatus.resultsSummary && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  {Object.entries(extractionStatus.resultsSummary).map(([key, value]) => (
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
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Extraction Started</h3>
          <p className="text-gray-500">
            Click "Run Extraction" to begin extracting database objects.
          </p>
        </div>
      )}
    </div>
  );
};

export default Extract;