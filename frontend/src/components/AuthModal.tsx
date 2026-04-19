import { useState } from 'react';
import { IoClose } from 'react-icons/io5';
import { useAuth } from '../context/AuthContext';

interface AuthModalProps {
  onClose: () => void;
  onSuccess?: () => void;
}

const AuthModal: React.FC<AuthModalProps> = ({ onClose, onSuccess }) => {
  const { login, register } = useAuth();
  const [isLoginMode, setIsLoginMode] = useState(true); // true = логин, false = регистрация
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError('Заполните все поля');
      return;
    }
    const success = login(username, password);
    if (success) {
      onClose();
      onSuccess?.();
    } else {
      setError('Неверное имя пользователя или пароль');
    }
  };

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !email || !password || !confirmPassword) {
      setError('Заполните все поля');
      return;
    }
    if (password !== confirmPassword) {
      setError('Пароли не совпадают');
      return;
    }
    const success = register(username, email, password);
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
          <h2>{isLoginMode ? 'Вход' : 'Регистрация'}</h2>
        </div>

        <form onSubmit={isLoginMode ? handleLogin : handleRegister}>
          <div className="modal-body">
            <label>Имя пользователя</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />

            {!isLoginMode && (
              <>
                <label>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </>
            )}

            <label>Пароль</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            {!isLoginMode && (
              <>
                <label>Подтверждение пароля</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </>
            )}

            {error && <div className="error-message">{error}</div>}
          </div>

          <div className="modal-footer">
            <button type="button" className="register-btn" onClick={() => { setIsLoginMode(false); setError(''); }}>
              Register
            </button>
            <button type="submit" className="save-btn">
              Log in
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AuthModal;