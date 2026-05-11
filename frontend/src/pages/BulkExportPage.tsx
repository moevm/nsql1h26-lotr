import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { axiosInstance } from '../api/axios-instance';

const BulkExportPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!user || user.role !== 'admin') {
    navigate('/');
    return null;
  }

  const handleExport = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axiosInstance.get('/bulk/export', {
        responseType: 'blob',
      });
      // Извлекаем имя файла из заголовка Content-Disposition
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'lotr-wiki-export.json';
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/);
        if (match && match[1]) filename = match[1];
      }
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Export failed: ' + (err.response?.data?.error?.message || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bulk-page">
      <h1>Mass Export</h1>
      <button onClick={handleExport} disabled={loading}>
        {loading ? 'Exporting...' : 'Download all data'}
      </button>
      {error && <div className="error-message">{error}</div>}
    </div>
  );
};

export default BulkExportPage;