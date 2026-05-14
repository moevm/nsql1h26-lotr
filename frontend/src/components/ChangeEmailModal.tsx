import { useState } from 'react';
import { IoClose } from 'react-icons/io5';
import { useAuth } from '../context/AuthContext';
import type { UpdateMeRequest } from '../api/generated/models';

interface ChangeEmailModalProps {
  onClose: () => void;
  onSuccess?: () => void;
}

const ChangeEmailModal: React.FC<ChangeEmailModalProps> = ({ onClose, onSuccess }) => {
  const { user, updateUser } = useAuth();
  const [email, setEmail] = useState(user?.email || '');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError('Email is required');
      return;
    }
    const updateData: UpdateMeRequest = { email };
    const success = await updateUser(updateData);
    if (success) {
      onClose();
      onSuccess?.();
    } else {
      setError('Failed to update email');
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <button className="modal-close-btn" onClick={onClose}>
            <IoClose size="24px" />
          </button>
          <h2>Change Email</h2>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <label>New Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            {error && <div className="error-message">{error}</div>}
          </div>
          <div className="modal-footer">
            <button type="submit" className="save-btn">Save</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChangeEmailModal;