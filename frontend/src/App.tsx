import { useState, useRef, useCallback } from 'react'
import './App.css'

interface DiagnosticsResult {
  status: string;
  stage_0?: {
    converted_columns: string[];
    flagged_columns: string[];
  };
  layer_1?: {
    dimensions: { rows: number; columns: number; memory_mb: number };
    feature_breakdown: { numeric: number; categorical: number; boolean: number; datetime: number };
    vitals: { missing_ratio: number; duplicate_ratio: number; constant_ratio: number };
    health_status: string;
    summary: string;
  };
  error?: string;
  message?: string;
}

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedFilename, setUploadedFilename] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDiagnosing, setIsDiagnosing] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{ type: 'success' | 'error' | 'info' | null; message: string }>({ type: null, message: '' });
  const [diagnosticsResult, setDiagnosticsResult] = useState<DiagnosticsResult | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      setSelectedFile(files[0]);
      setUploadedFilename(null);
      setDiagnosticsResult(null);
      setUploadStatus({ type: 'info', message: `Selected: ${files[0].name}` });
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setSelectedFile(files[0]);
      setUploadedFilename(null);
      setDiagnosticsResult(null);
      setUploadStatus({ type: 'info', message: `Selected: ${files[0].name}` });
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadStatus({ type: 'info', message: 'Uploading...' });

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
      }

      setUploadedFilename(selectedFile.name);
      setUploadStatus({ type: 'success', message: `✓ "${selectedFile.name}" uploaded successfully` });
    } catch (error) {
      setUploadStatus({ type: 'error', message: `✗ Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}` });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDiagnose = async () => {
    if (!uploadedFilename) return;

    setIsDiagnosing(true);
    setUploadStatus({ type: 'info', message: 'Running diagnostics...' });
    setDiagnosticsResult(null);

    try {
      const response = await fetch('/diagnose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: uploadedFilename }),
      });

      if (!response.ok) {
        throw new Error(`Diagnostics failed: ${response.status}`);
      }

      const result: DiagnosticsResult = await response.json();
      setDiagnosticsResult(result);

      if (result.status === 'success') {
        setUploadStatus({ type: 'success', message: '✓ Diagnostics complete!' });
      } else {
        setUploadStatus({ type: 'error', message: `✗ ${result.message || 'Diagnostics failed'}` });
      }
    } catch (error) {
      setUploadStatus({ type: 'error', message: `✗ Diagnostics error: ${error instanceof Error ? error.message : 'Unknown error'}` });
    } finally {
      setIsDiagnosing(false);
    }
  };

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'GREEN': return '#10b981';
      case 'YELLOW': return '#f59e0b';
      case 'RED': return '#ef4444';
      case 'EXTREME': return '#7c3aed';
      default: return '#6b7280';
    }
  };

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <div className="logo">
            <span className="logo-icon">⚡</span>
            <h1>ML Diagnostic</h1>
          </div>
          <p className="tagline">Intelligent dataset analysis powered by machine learning</p>
        </header>

        <div className="main-card">
          {/* Upload Area */}
          <div
            className={`drop-zone ${isDragging ? 'dragging' : ''} ${selectedFile ? 'has-file' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept=".csv,.xlsx,.xls,.json,.parquet,.tsv"
              hidden
            />
            <div className="drop-icon">
              {selectedFile ? '📄' : '📁'}
            </div>
            <div className="drop-text">
              {selectedFile ? selectedFile.name : 'Drop your dataset here'}
            </div>
            <div className="drop-subtext">
              {selectedFile
                ? `${(selectedFile.size / 1024).toFixed(1)} KB`
                : 'or click to browse • Supports CSV, Excel, JSON, Parquet'}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="actions">
            {selectedFile && !uploadedFilename && (
              <button
                className="btn btn-primary"
                onClick={handleUpload}
                disabled={isUploading}
              >
                {isUploading ? (
                  <><span className="spinner"></span> Uploading...</>
                ) : (
                  <>📤 Upload File</>
                )}
              </button>
            )}

            {uploadedFilename && (
              <button
                className="btn btn-accent"
                onClick={handleDiagnose}
                disabled={isDiagnosing}
              >
                {isDiagnosing ? (
                  <><span className="spinner"></span> Analyzing...</>
                ) : (
                  <>🔬 Run Diagnostics</>
                )}
              </button>
            )}
          </div>

          {/* Status Message */}
          {uploadStatus.type && (
            <div className={`status-message ${uploadStatus.type}`}>
              {uploadStatus.message}
            </div>
          )}

          {/* Results Display */}
          {diagnosticsResult && diagnosticsResult.status === 'success' && diagnosticsResult.layer_1 && (
            <div className="results">
              <div className="results-header">
                <h2>📊 Analysis Results</h2>
                <span
                  className="health-badge"
                  style={{ backgroundColor: getHealthColor(diagnosticsResult.layer_1.health_status) }}
                >
                  {diagnosticsResult.layer_1.health_status}
                </span>
              </div>

              <div className="results-grid">
                <div className="result-card">
                  <h3>📐 Dimensions</h3>
                  <div className="stat-row">
                    <span>Rows</span>
                    <strong>{diagnosticsResult.layer_1.dimensions.rows.toLocaleString()}</strong>
                  </div>
                  <div className="stat-row">
                    <span>Columns</span>
                    <strong>{diagnosticsResult.layer_1.dimensions.columns}</strong>
                  </div>
                  <div className="stat-row">
                    <span>Memory</span>
                    <strong>{diagnosticsResult.layer_1.dimensions.memory_mb} MB</strong>
                  </div>
                </div>

                <div className="result-card">
                  <h3>🧮 Features</h3>
                  <div className="stat-row">
                    <span>Numeric</span>
                    <strong>{diagnosticsResult.layer_1.feature_breakdown.numeric}</strong>
                  </div>
                  <div className="stat-row">
                    <span>Categorical</span>
                    <strong>{diagnosticsResult.layer_1.feature_breakdown.categorical}</strong>
                  </div>
                  <div className="stat-row">
                    <span>Boolean</span>
                    <strong>{diagnosticsResult.layer_1.feature_breakdown.boolean}</strong>
                  </div>
                </div>

                <div className="result-card">
                  <h3>🩺 Data Health</h3>
                  <div className="stat-row">
                    <span>Missing</span>
                    <strong>{(diagnosticsResult.layer_1.vitals.missing_ratio * 100).toFixed(1)}%</strong>
                  </div>
                  <div className="stat-row">
                    <span>Duplicates</span>
                    <strong>{(diagnosticsResult.layer_1.vitals.duplicate_ratio * 100).toFixed(1)}%</strong>
                  </div>
                  <div className="stat-row">
                    <span>Constant</span>
                    <strong>{(diagnosticsResult.layer_1.vitals.constant_ratio * 100).toFixed(1)}%</strong>
                  </div>
                </div>
              </div>

              <div className="summary-box">
                <strong>Summary:</strong> {diagnosticsResult.layer_1.summary}
              </div>
            </div>
          )}
        </div>

        <footer className="footer">
          <p>ML Diagnostic System v1.0</p>
        </footer>
      </div>
    </div>
  )
}

export default App
