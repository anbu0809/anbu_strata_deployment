export interface Connection {
  id: number;
  name: string;
  dbType: string;
}

export interface Session {
  source: Connection | null;
  target: Connection | null;
}

export interface AnalysisStatus {
  ok: boolean;
  phase: string | null;
  percent: number | null;
  done: boolean | null;
  resultsSummary: Record<string, any> | null;
}

export interface ValidationItem {
  category: string;
  status: 'Pass' | 'Fail' | 'Warning';
  errorDetails: string | null;
  suggestedFix: string | null;
  confidenceScore: number;
}

export type DatabaseType = 
  | 'PostgreSQL'
  | 'MySQL'
  | 'Snowflake'
  | 'Databricks'
  | 'Oracle'
  | 'SQL Server'
  | 'Teradata'
  | 'Google BigQuery';