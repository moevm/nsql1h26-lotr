import React from 'react';
import { IoClose } from 'react-icons/io5';

interface ErrorModalProps {
  message: string;
  statusCode?: number;
  onClose: () => void;
}

const ErrorModal: React.FC<ErrorModalProps> = ({ message, statusCode, onClose }) => {
  const title = statusCode ? `Error ${statusCode}` : 'Error';

  return (
    <div className="modal-overlay">
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <button className="modal-close-btn" onClick={onClose}>
            <IoClose size="24px" />
          </button>
          <h2>{title}</h2>
        </div>
        <div className="modal-body error-modal-body">
          <img src="/images/error.gif" alt="Error" className="error-gif" />
          <p>{message}</p>
        </div>
      </div>
    </div>
  );
};

export default ErrorModal;