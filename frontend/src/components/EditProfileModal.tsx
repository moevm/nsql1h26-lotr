import { useState } from 'react';
import { IoClose } from 'react-icons/io5';
import { useAuth } from '../context/AuthContext';
import type { UpdateMeRequest } from '../api/generated/models';

interface EditProfileModalProps {
  onClose: () => void;
  onSuccess?: () => void;
}

const EditProfileModal: React.FC<EditProfileModalProps> = ({ onClose, onSuccess }) => {
  const { user, updateUser } = useAuth();
  const [email, setEmail] = useState(user?.email || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError('Email обязателен');
      return;
    }
    if (!currentPassword) {
      setError('Текущий пароль обязателен для любых изменений');
      return;
    }
    if (newPassword && newPassword !== confirmPassword) {
      setError('Новый пароль и подтверждение не совпадают');
      return;
    }
    const updateData: UpdateMeRequest = {
      email,
      password_current: currentPassword,
    };
    if (newPassword) {
      updateData.password = newPassword;
    }
    const success = await updateUser(updateData);
    if (success) {
      onClose();
      onSuccess?.();
    } else {
      setError('Не удалось обновить профиль. Проверьте правильность текущего пароля.');
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <button className="modal-close-btn" onClick={onClose}>
            <IoClose size="24px" />
          </button>
          <h2>Редактировать профиль</h2>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <label>Текущий пароль (обязательно)</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
            <label>Новый пароль (оставьте пустым, чтобы не менять)</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <label>Подтверждение нового пароля</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
            {error && <div className="error-message">{error}</div>}
          </div>
          <div className="modal-footer">
            <button type="submit" className="save-btn">
              Сохранить
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditProfileModal;