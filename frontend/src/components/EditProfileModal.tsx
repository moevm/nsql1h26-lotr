import { useState } from 'react';
import { IoClose } from 'react-icons/io5';
import { useAuth } from '../context/AuthContext';

interface EditProfileModalProps {
  onClose: () => void;
  onSuccess?: () => void;
}

const EditProfileModal: React.FC<EditProfileModalProps> = ({ onClose, onSuccess }) => {
  const { user, updateUser } = useAuth();
  const [username, setUsername] = useState(user?.username || '');
  const [email, setEmail] = useState(user?.email || '');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !email) {
      setError('Имя пользователя и email обязательны');
      return;
    }
    if (password && password !== confirmPassword) {
      setError('Пароли не совпадают');
      return;
    }
    const success = updateUser(username, email, password || undefined);
    if (success) {
      onClose();
      onSuccess?.();
    } else {
      setError('Пользователь с таким именем уже существует');
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
            <label>Имя пользователя</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <label>Новый пароль (оставьте пустым, чтобы не менять)</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
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