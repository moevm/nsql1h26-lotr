import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaUserShield } from 'react-icons/fa';
import { TbDownload, TbUpload } from "react-icons/tb";
import { axiosInstance } from '../api/axios-instance';
import { useToast } from '../context/ToastContext';

interface AdminDropdownProps {
  isOpen: boolean;
  onClose: () => void;
  onError: (message: string, statusCode?: number) => void;
}

const AdminDropdown: React.FC<AdminDropdownProps> = ({ isOpen, onClose, onError }) => {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [importing, setImporting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, onClose]);

  const handleExport = async () => {
    // Не закрываем меню до завершения
    try {
      const response = await axiosInstance.get('/bulk/export', {
        responseType: 'blob',
      });
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
      onClose();
    } catch (err: any) {
      console.error('Export error:', err);
      const statusCode = err.response?.status;
      const message = err.response?.data?.error?.message || err.message || 'Export failed';
      onError(message, statusCode);
      onClose();
    }
  };

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) {
      onClose();
      return;
    }
    setImporting(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axiosInstance.post('/bulk/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const result = response.data;
      showToast('Import completed');
      if (result.errors?.length) {
        console.warn('Import errors:', result.errors);
      }
      onClose();
    } catch (err: any) {
      console.error('Import error:', err);
      const statusCode = err.response?.status;
      let message = err.response?.data?.error?.message || err.message || 'Import failed';
      if (err.response?.data?.message) {
        message = err.response.data.message;
      }
      onError(message, statusCode);
      onClose();
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleAdminPanel = () => {
    onClose();
    navigate('/admin');
  };

  if (!isOpen) return null;

  return (
    <div className="dropdown-menu" ref={menuRef}>
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        accept=".json"
        onChange={handleFileChange}
      />
      <button onClick={handleImportClick} className="dropdown-item" disabled={importing}>
        <TbDownload /> {importing ? 'Importing...' : 'Bulk import'}
      </button>
      <button onClick={handleExport} className="dropdown-item">
        <TbUpload /> Bulk export
      </button>
      <button onClick={handleAdminPanel} className="dropdown-item">
        <FaUserShield /> Admin panel
      </button>
    </div>
  );
};

export default AdminDropdown;