import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || '';

function AdminUserManagement({ user }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ username: '', password: '', email: '', is_staff: false });
  const [creating, setCreating] = useState(false);

  const access = localStorage.getItem('access');

  useEffect(() => {
    if (user && (user.is_staff || user.is_superuser)) {
      fetchUsers();
    }
    // eslint-disable-next-line
  }, [user]);

  const fetchUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.get(`${API_BASE}/api/users/`, {
        headers: { Authorization: `Bearer ${access}` },
      });
      setUsers(res.data);
    } catch (err) {
      setError('Failed to fetch users.');
    }
    setLoading(false);
  };

  const handleInputChange = e => {
    const { name, value, type, checked } = e.target;
    setForm(f => ({ ...f, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleCreateUser = async e => {
    e.preventDefault();
    setCreating(true);
    setError('');
    try {
      await axios.post(`${API_BASE}/api/users/create/`, form, {
        headers: { Authorization: `Bearer ${access}` },
      });
      setForm({ username: '', password: '', email: '', is_staff: false });
      fetchUsers();
    } catch (err) {
      setError('Failed to create user. (Only superusers can create users)');
    }
    setCreating(false);
  };

  const handleDeleteUser = async userId => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    setError('');
    try {
      await axios.delete(`${API_BASE}/api/users/${userId}/delete/`, {
        headers: { Authorization: `Bearer ${access}` },
      });
      fetchUsers();
    } catch (err) {
      setError('Failed to delete user.');
    }
  };

  if (!user || (!user.is_staff && !user.is_superuser)) {
    return <div style={{ padding: 32, color: 'red' }}>You do not have permission to view this page.</div>;
  }

  return (
    <div style={{ maxWidth: 600, margin: '40px auto', background: '#fff', borderRadius: 8, boxShadow: '0 2px 8px #eee', padding: 24 }}>
      <h2>User Management</h2>
      {error && <div style={{ color: 'red', marginBottom: 12 }}>{error}</div>}
      {user.is_superuser && (
        <form onSubmit={handleCreateUser} style={{ marginBottom: 24 }}>
          <h4>Create New User</h4>
          <input
            type="text"
            name="username"
            placeholder="Username"
            value={form.username}
            onChange={handleInputChange}
            required
            style={{ marginRight: 8 }}
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={form.password}
            onChange={handleInputChange}
            required
            style={{ marginRight: 8 }}
          />
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={form.email}
            onChange={handleInputChange}
            style={{ marginRight: 8 }}
          />
          <label style={{ marginRight: 8 }}>
            <input
              type="checkbox"
              name="is_staff"
              checked={form.is_staff}
              onChange={handleInputChange}
            />{' '}
            Staff
          </label>
          <button type="submit" disabled={creating}>Create</button>
        </form>
      )}
      <h4>All Users</h4>
      {loading ? (
        <div>Loading users...</div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#f5f5f5' }}>
              <th style={{ padding: 8, border: '1px solid #eee' }}>Username</th>
              <th style={{ padding: 8, border: '1px solid #eee' }}>Email</th>
              <th style={{ padding: 8, border: '1px solid #eee' }}>Staff</th>
              <th style={{ padding: 8, border: '1px solid #eee' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id}>
                <td style={{ padding: 8, border: '1px solid #eee' }}>{u.username}</td>
                <td style={{ padding: 8, border: '1px solid #eee' }}>{u.email}</td>
                <td style={{ padding: 8, border: '1px solid #eee' }}>{u.is_staff ? 'Yes' : 'No'}</td>
                <td style={{ padding: 8, border: '1px solid #eee' }}>
                  {(user.is_superuser || user.is_staff) && (
                    <button onClick={() => handleDeleteUser(u.id)} style={{ color: 'red' }}>Delete</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default AdminUserManagement; 