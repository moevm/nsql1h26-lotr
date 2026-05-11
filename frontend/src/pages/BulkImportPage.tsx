// src/pages/BulkImportPage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { axiosInstance } from '../api/axios-instance';
import { FaFileAlt, FaTimes } from 'react-icons/fa';

const BulkImportPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  if (!user || user.role !== 'admin') {
    navigate('/');
    return null;
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError('');
    } else {
      setFile(null);
    }
  };

  const handleClearFile = () => {
    setFile(null);
    setResult(null);
    setError('');
    // очищаем input, чтобы при повторном выборе того же файла сработал onChange
    const fileInput = document.getElementById('import-file') as HTMLInputElement;
    if (fileInput) fileInput.value = '';
  };

  const handleImport = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }
    setLoading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axiosInstance.post('/bulk/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(response.data);
    } catch (err: any) {
      setError('Import failed: ' + (err.response?.data?.error?.message || err.message));
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="bulk-page">
      <h1>Mass Import</h1>
      <div className="import-form">
        <input
          type="file"
          id="import-file"
          accept=".json"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
        <label htmlFor="import-file" className="file-input-label">
          Choose file
        </label>
        {file && (
          <div className="selected-file">
            <FaFileAlt className="file-icon" />
            <span className="file-name" title={file.name}>{file.name}</span>
            <span className="file-size">({formatFileSize(file.size)})</span>
            <button className="clear-file-btn" onClick={handleClearFile} title="Clear">
              <FaTimes />
            </button>
          </div>
        )}
        <button onClick={handleImport} disabled={loading || !file}>
          {loading ? 'Importing...' : 'Import'}
        </button>
      </div>
      {error && <div className="error-message">{error}</div>}
      {result && (
        <div className="import-result">
          <h3>Import result</h3>
          <p><strong>Imported:</strong> {JSON.stringify(result.imported)}</p>
          <p><strong>Skipped:</strong> {result.skipped}</p>
          {result.errors && result.errors.length > 0 && (
            <div>
              <h4>Errors:</h4>
              <ul>
                {result.errors.map((err: any, idx: number) => (
                  <li key={idx}>{err.slug}: {err.reason}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default BulkImportPage;