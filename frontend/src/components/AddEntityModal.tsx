import { useState } from 'react';
import { IoClose } from 'react-icons/io5';

interface AddEntityModalProps {
  title: string;      // "Персонажа", "Предмет" и т.д.
  onClose: () => void;
  onSave: (data: any) => void;   // пока заглушка
}

const AddEntityModal: React.FC<AddEntityModalProps> = ({ title, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    name: '',
    race: '',
    gender: '',
    description: ''
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);   // заглушка
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <button className="modal-close-btn" onClick={onClose}>
            <IoClose size="24px" />
          </button>
          <h2>Добавить {title}</h2>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <label>Имя *</label>
            <input name="name" value={formData.name} onChange={handleChange} required />

            <label>Раса</label>
            <input name="race" value={formData.race} onChange={handleChange} placeholder="например, Хоббит" />

            <label>Пол</label>
            <div className="radio-group">
              <label><input type="radio" name="gender" value="male" onChange={handleChange} /> Мужской</label>
              <label><input type="radio" name="gender" value="female" onChange={handleChange} /> Женский</label>
              <label><input type="radio" name="gender" value="other" onChange={handleChange} /> Другой</label>
            </div>

            <label>Общая информация</label>
            <textarea name="description" rows={4} value={formData.description} onChange={handleChange} />
          </div>
          <div className="modal-footer">
            <button type="submit" className="save-btn">Сохранить</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddEntityModal;