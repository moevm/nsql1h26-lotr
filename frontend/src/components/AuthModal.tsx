import { useState } from 'react';
import { IoClose } from 'react-icons/io5';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import ErrorModal from './ErrorModal';

interface AuthModalProps {
  onClose: () => void;
  onSuccess?: () => void;
}

const AuthModal: React.FC<AuthModalProps> = ({ onClose, onSuccess }) => {
  const { login, register } = useAuth();
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const { showToast } = useToast();
  const [errorModal, setErrorModal] = useState<{ status?: number; message: string } | null>(null);

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!username || !password) {
      setError('Fill in all fields');
      return;
    }
    const success = await login(username, password);
    if (success.success) {
      showToast('User successfully authorized!');
      onClose();
      onSuccess?.();
    } else {
      setErrorModal({ status: success.status, message: success.message || 'Login failed' });
    }
  };

  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!username || !email || !password || !confirmPassword) {
      setError('Fill in all fields');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    const success = await register(username, email, password);
    if (success.success) {
      showToast('User successfully registered!');
      onClose();
      onSuccess?.();
    } else {
      setErrorModal({ status: success.status, message: success.message || 'Registration failed' });
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <button className="modal-close-btn" onClick={onClose}>
            <IoClose size="24px" />
          </button>
          <h2>{isLoginMode ? 'Login' : 'Registration'}</h2>
        </div>

        <form onSubmit={isLoginMode ? handleLogin : handleRegister}>
          <div className="modal-body">
            <label>Username</label>
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

            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            {!isLoginMode && (
              <>
                <label>Confirm password</label>
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
          {errorModal && (
            <ErrorModal
              message={errorModal.message}
              statusCode={errorModal.status}
              onClose={() => setErrorModal(null)}
            />
          )}

          <div className="modal-footer">
            <button
              type="button"
              className="save-btn"
              onClick={() => {
                setIsLoginMode(!isLoginMode);
                setError('');
              }}
            >
              {isLoginMode ? 'Register' : 'Back to Login'}
            </button>
            <button type="submit" className="save-btn">
              {isLoginMode ? 'Log in' : 'Register'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AuthModal;