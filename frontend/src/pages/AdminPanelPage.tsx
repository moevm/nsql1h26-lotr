import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useListUsers, useUpdateUserRole, useDeleteUser } from '../api/generated/users/users';
import { useToast } from '../context/ToastContext';
import { useAuth } from '../context/AuthContext';
import type { AdminUser } from '../api/generated/models';

const AdminPanelPage: React.FC = () => {
  const { user: currentUser } = useAuth();
  const { showToast } = useToast();
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const { data, isLoading, error, refetch } = useListUsers({ page, page_size: pageSize });
  const updateRoleMutation = useUpdateUserRole();
  const deleteUserMutation = useDeleteUser();

  const users = data?.results || [];
  const totalCount = data?.count || 0;
  const hasPrev = data?.previous !== null;
  const hasNext = data?.next !== null;

  const handlePrevPage = () => { if (hasPrev) setPage(p => p - 1); };
  const handleNextPage = () => { if (hasNext) setPage(p => p + 1); };

  const handleRoleChange = async (username: string, newRole: 'viewer' | 'admin') => {
    // Запретить смену своей роли
    if (username === currentUser?.username) {
      showToast('You cannot change your own role.');
      return;
    }
    if (!confirm(`Change role of ${username} to ${newRole}?`)) return;
    try {
      await updateRoleMutation.mutateAsync({ username, data: { role: newRole } });
      showToast(`Role of ${username} updated to ${newRole}`);
      refetch();
    } catch (err: any) {
      showToast(`Failed to update role: ${err.response?.data?.error?.message || err.message}`);
    }
  };

  const handleDeleteUser = async (username: string) => {
    if (username === currentUser?.username) {
      showToast('You cannot delete your own account.');
      return;
    }
    if (!confirm(`Delete user ${username}? This action is irreversible.`)) return;
    try {
      await deleteUserMutation.mutateAsync({ username });
      showToast(`User ${username} deleted.`);
      refetch();
    } catch (err: any) {
      showToast(`Failed to delete user: ${err.response?.data?.error?.message || err.message}`);
    }
  };

  if (isLoading) return <div className="loader">Loading users...</div>;
  if (error) return <div className="error">Failed to load users.</div>;

  return (
    <div className="admin-panel">
      <h1 className="catalog-title">Admin Panel</h1>
      <div className="users-table-container">
        <table className="users-table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
              <th>Created at</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user: AdminUser) => (
              <tr key={user.username}>
                <td>
                  <Link to={`/admin/users/${user.username}`} className="user-link">
                    {user.username}
                  </Link>
                </td>
                <td>{user.email}</td>
                <td>
                  <select
                    value={user.role}
                    onChange={(e) => handleRoleChange(user.username, e.target.value as 'viewer' | 'admin')}
                    disabled={user.username === currentUser?.username}
                    className="role-select"
                  >
                    <option value="viewer">Viewer</option>
                    <option value="admin">Admin</option>
                  </select>
                </td>
                <td>{new Date(user.created_at).toLocaleDateString()}</td>
                <td>
                  <button
                    onClick={() => handleDeleteUser(user.username)}
                    className="delete-user-btn"
                    disabled={user.username === currentUser?.username}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="pagination-container">
        <button className="pagination-btn" onClick={handlePrevPage} disabled={!hasPrev}>← Previous</button>
        <span className="pagination-info">Page {page} (total: {Math.ceil(totalCount / pageSize)})</span>
        <button className="pagination-btn" onClick={handleNextPage} disabled={!hasNext}>Next →</button>
      </div>
    </div>
  );
};

export default AdminPanelPage;