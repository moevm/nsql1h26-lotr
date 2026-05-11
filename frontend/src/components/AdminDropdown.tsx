// src/components/AdminDropdown.tsx
import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaFileImport, FaFileExport, FaUserShield } from 'react-icons/fa';
import { axiosInstance } from '../api/axios-instance';
import { useToast } from '../context/ToastContext';

interface AdminDropdownProps {
  isOpen: boolean;
  onClose: () => void;
}

const AdminDropdown: React.FC<AdminDropdownProps> = ({ isOpen, onClose }) => {
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
    onClose();
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
      showToast('Export started successfully!');
    } catch (err: any) {
      console.error('Export error:', err);
      showToast('Export failed: ' + (err.response?.data?.error?.message || err.message));
    }
  };

  const handleImportClick = () => {
    // Не закрываем меню, чтобы компонент не размонтировался до выбора файла
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) {
      onClose(); // если отмена, закрываем меню
      return;
    }
    onClose(); // закрываем меню сразу после выбора файла
    setImporting(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axiosInstance.post('/bulk/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const result = response.data;
      const importedCount = Object.values(result.imported || {}).reduce((a: number, b: number) => a + b, 0);
      showToast(`Import completed: ${importedCount} items imported, ${result.skipped || 0} skipped.`);
      if (result.errors?.length) {
        console.warn('Import errors:', result.errors);
      }
    } catch (err: any) {
      console.error('Import error:', err);
      showToast('Import failed: ' + (err.response?.data?.error?.message || err.message));
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
        <FaFileImport /> {importing ? 'Importing...' : 'Mass import'}
      </button>
      <button onClick={handleExport} className="dropdown-item">
        <FaFileExport /> Mass export
      </button>
      <button onClick={handleAdminPanel} className="dropdown-item">
        <FaUserShield /> Admin panel
      </button>
    </div>
  );
};

export default AdminDropdown;