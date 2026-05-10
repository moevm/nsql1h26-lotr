// src/pages/CreateCategoryPage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateCategory } from '../api/generated/categories/categories';
import { useToast } from '../context/ToastContext';
import ErrorModal from '../components/ErrorModal';
import { useAuth } from '../context/AuthContext';

const CreateCategoryPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [parentSlug, setParentSlug] = useState('');
  const [errorModalOpen, setErrorModalOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [errorStatusCode, setErrorStatusCode] = useState<number | undefined>(undefined);
  const createCategory = useCreateCategory();

  if (!user || user.role !== 'admin') {
    navigate('/categories');
    return null;
  }

  // Генерация slug из названия
  const generateSlug = (input: string): string => {
    return input
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')   // убираем спецсимволы
      .replace(/\s+/g, '-')       // пробелы -> дефисы
      .replace(/-+/g, '-');       // убираем повторяющиеся дефисы
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setErrorMessage('Name is required');
      setErrorModalOpen(true);
      return;
    }

    const slug = generateSlug(name);

    try {
      await createCategory.mutateAsync({
        data: {
          slug,
          name: name.trim(),
          description: description.trim() || undefined,
          parent_slug: parentSlug.trim() || undefined,
        },
      });
      showToast('Category created successfully!');
      navigate('/categories');
    } catch (err: any) {
      const serverError = err.response?.data;
      let msg = 'Creation failed.';
      if (serverError?.error?.message) msg = serverError.error.message;
      else if (serverError?.message) msg = serverError.message;
      else if (typeof serverError === 'string') msg = serverError;
      setErrorStatusCode(err.response?.status);
      setErrorMessage(msg);
      setErrorModalOpen(true);
    }
  };

  return (
    <div className="edit-page">
      <h1>Create a new category</h1>
      <form onSubmit={handleSubmit}>
        <section className="basic-info">
          <label>Name *</label>
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            required
          />
        </section>
        <section className="basic-info">
          <label>Description</label>
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            rows={3}
          />
        </section>
        <section className="basic-info">
          <label>Parent category (slug, optional)</label>
          <input
            value={parentSlug}
            onChange={e => setParentSlug(e.target.value)}
          />
        </section>
        <div className="edit-actions">
          <button type="submit" disabled={createCategory.isPending}>
            {createCategory.isPending ? 'Creating...' : 'Create'}
          </button>
          <button type="button" onClick={() => navigate('/categories')}>
            Cancel
          </button>
        </div>
      </form>
      {errorModalOpen && (
        <ErrorModal
          message={errorMessage}
          statusCode={errorStatusCode}
          onClose={() => setErrorModalOpen(false)}
        />
      )}
    </div>
  );
};

export default CreateCategoryPage;