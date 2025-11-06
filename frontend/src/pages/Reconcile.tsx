import { useState, useEffect, useRef } from 'react';
import { Play, CheckCircle, AlertCircle, Download, Database, Server } from 'lucide-react';
import { ValidationItem } from '../types';

export default function Reconcile() {
  const [isRunning, setIsRunning] = useState(false);
  const [validationResults, setValidationResults] = useState<ValidationItem[]>([]);
  const [canExport, setCanExport] = useState(false);
  const [validationStatus, setValidationStatus] = useState({
    phase: '',
    percent: 0,
    done: false,
    error: null as string | null
  });
  
  // Use ref to store interval ID
  const pollIntervalRef = useRef<number | null>(null);

  // Only fetch validation status when user manually clicks Run Validation
  // REMOVED: Auto-start validation on page load
  useEffect(() => {
    // No automatic validation calls - validation is manual only
    return () => {
      // Cleanup interval on component unmount
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  // Only fetch validation status when validation is actually running
  const fetchValidationStatus = async () => {
    try {
      const response = await fetch('/api/validate/status');
      if (response.ok) {
        const data = await response.json();
        setValidationStatus(data);
        console.log('Validation status:', data); // Debug log
        // If validation is done, stop the running state and polling
        if (data.done) {
          setIsRunning(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          // Fetch results after completion
          fetchValidationResults();
        }
      } else {
        console.error('Validation status response not ok:', response.status);
      }
    } catch (error) {
      console.error('Failed to fetch validation status:', error);
    }
  };

  const fetchValidationResults = async () => {
    try {
      const response = await fetch('/api/validate/report');
      if (response.ok) {
        const data = await response.json();
        console.log('Validation results:', data); // Debug log
        setValidationResults(data);
        if (data.length > 0) {
          setCanExport(true);
        }
      } else {
        console.error('Validation results response not ok:', response.status);
      }
    } catch (error) {
      console.error('Failed to fetch validation results:', error);
    }
  };

  const handleRunValidation = async () => {
    console.log('Starting validation...'); // Debug log
    setIsRunning(true);
    setValidationResults([]);
    setCanExport(false);
    setValidationStatus({
      phase: 'Initializing',
      percent: 0,
      done: false,
      error: null
    });
    
    // Clear any existing interval
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
    
    try {
      const response = await fetch('/api/validate/run', {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to start validation');
      }
      
      console.log('Validation started successfully, beginning polling...'); // Debug log
      
      // Start polling for status updates immediately
      pollIntervalRef.current = setInterval(() => {
        console.log('Polling validation status...'); // Debug log
        fetchValidationStatus();
      }, 2000);
      
      // Also fetch status immediately
      fetchValidationStatus();
      
    } catch (error) {
      console.error('Failed to start validation:', error);
      setIsRunning(false);
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }
  };

  const handleExport = async (format: 'pdf' | 'json' | 'xlsx') => {
    try {
      const response = await fetch(`/api/export/${format}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `validation_report.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error(`Failed to export ${format}:`, error);
    }
  };

  // Group results by category for better organization
  const groupedResults = validationResults.reduce((acc, item) => {
    const category = item.category.split(' - ')[0]; // Extract main category
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(item);
    return acc;
  }, {} as Record<string, ValidationItem[]>);

  // Determine if validation is currently running
  const isValidationRunning = isRunning || (validationStatus.percent > 0 && !validationStatus.done);

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#085690] mb-2">Reconcile</h1>
        <p className="text-gray-600">Validate migration results and generate reports</p>
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold text-[#085690]">Validation</h2>
            <p className="text-gray-600">Run comprehensive validation checks</p>
          </div>
          
          <button
            onClick={handleRunValidation}
            disabled={isValidationRunning}
            className="px-4 py-2 bg-[#085690] text-white rounded-md hover:bg-[#064a7a] disabled:opacity-50 flex items-center"
          >
            {isValidationRunning ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {validationStatus.phase || 'Running Validation...'}
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Run Validation
              </>
            )}
          </button>
        </div>
        
        {/* Progress bar */}
        {validationStatus.percent > 0 && !validationStatus.done && (
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>{validationStatus.phase}</span>
              <span>{validationStatus.percent}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-[#085690] h-2 rounded-full transition-all duration-300" 
                style={{ width: `${validationStatus.percent}%` }}
              ></div>
            </div>
          </div>
        )}
        
        {/* Error message */}
        {validationStatus.error && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-md">
            <strong>Error:</strong> {validationStatus.error}
          </div>
        )}
      </div>
      
      {validationResults.length > 0 ? (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <div className="rounded-full bg-[#085690] p-3">
                  <CheckCircle className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Passed</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {validationResults.filter(r => r.status === 'Pass').length}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <div className="rounded-full bg-[#ec6225] p-3">
                  <AlertCircle className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Failed</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {validationResults.filter(r => r.status === 'Fail').length}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <div className="rounded-full bg-[#085690] p-3">
                  <Database className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Tests</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {validationResults.length}
                  </p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Detailed Results */}
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="px-6 py-4 border-b">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-[#085690]">Validation Results</h2>
                {canExport && (
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleExport('pdf')}
                      className="px-3 py-1 text-sm bg-[#ec6225] text-white rounded-md hover:bg-[#d4551e] flex items-center"
                    >
                      <Download className="h-4 w-4 mr-1" />
                      PDF
                    </button>
                    <button
                      onClick={() => handleExport('json')}
                      className="px-3 py-1 text-sm bg-[#085690] text-white rounded-md hover:bg-[#064a7a] flex items-center"
                    >
                      <Download className="h-4 w-4 mr-1" />
                      JSON
                    </button>
                    <button
                      onClick={() => handleExport('xlsx')}
                      className="px-3 py-1 text-sm bg-[#085690] text-white rounded-md hover:bg-[#064a7a] flex items-center"
                    >
                      <Download className="h-4 w-4 mr-1" />
                      XLSX
                    </button>
                  </div>
                )}
              </div>
            </div>
            
            {/* Grouped Results */}
            <div className="divide-y divide-gray-200">
              {Object.entries(groupedResults).map(([category, items]) => (
                <div key={category} className="p-6">
                  <h3 className="text-lg font-medium text-[#085690] mb-4 flex items-center">
                    <Server className="h-5 w-5 mr-2 text-[#085690]" />
                    {category}
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-[#085690] uppercase tracking-wider">
                            Test
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-[#085690] uppercase tracking-wider">
                            Status
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-[#085690] uppercase tracking-wider">
                            Error Details
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-[#085690] uppercase tracking-wider">
                            Suggested Fix
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-[#085690] uppercase tracking-wider">
                            Confidence
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {items.map((item, index) => (
                          <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {item.category.split(' - ')[1] || item.category}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                item.status === 'Pass' 
                                  ? 'bg-[#085690] text-white' 
                                  : 'bg-[#ec6225] text-white'
                              }`}>
                                {item.status}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-500 max-w-xs">
                              {item.errorDetails || '-'}
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-500 max-w-xs">
                              {item.suggestedFix || '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {item.confidenceScore}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Validation Results</h3>
          <p className="text-gray-500">
            Run validation to check migration results and generate a report.
          </p>
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