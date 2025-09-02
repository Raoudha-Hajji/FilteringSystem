import React, { useEffect, useState, useMemo } from 'react';
import './Filtered.css';
import axios from 'axios';
import { MaterialReactTable } from 'material-react-table';

const API_BASE = process.env.REACT_APP_API_URL || '';

function Rejected({ user }) {
  const [data, setData] = useState([]);
  const [keywords, setKeywords] = useState([]);
  const [newKeyword, setNewKeyword] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const access = localStorage.getItem('access');

  // --- Fetch Rejected Data ---
  const fetchRejectedData = async () => {
    setIsLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/sorter/api/rejected_data/`);
      setData(res.data);
    } catch (err) {
      console.error('Error fetching data:', err);
      setData([]);
    } finally {
      setIsLoading(false);
    }
  };

  // --- Fetch Keywords ---
  const fetchKeywords = async () => {
    try {
      const res = await axios.get(`${API_BASE}/sorter/api/keywords/`, {
        headers: access ? { Authorization: `Bearer ${access}` } : {},
      });
      setKeywords(res.data);
    } catch (err) {
      console.error('Error fetching keywords:', err);
      setKeywords([]);
    }
  };

  // --- Feedback ---
  const handleFeedback = async (row, label) => {
    try {
      await axios.post(`${API_BASE}/sorter/api/feedback/`, {
        consultation_id: row.consultation_id,
        client: row.client,
        intitule_projet: row.intitule_projet,
        lien: row.lien,
        Selection: label
      }, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${access}`,
        }
      });
      
      // Remove the kept row from the rejected data
      setData(prevData => prevData.filter(item => item.consultation_id !== row.consultation_id));
      
      alert(`Row kept and moved to filtered table. Feedback saved as ${label === 1 ? 'Keep' : 'Reject'}`);
    } catch (error) {
      console.error("Error sending feedback:", error);
      alert("Failed to send feedback.");
    }
  };

  // --- Add / Delete Keywords ---
  const handleAddKeyword = async () => {
    if (!newKeyword.trim()) return;
    if (!user || (!user.is_staff && !user.is_superuser)) return;
    await axios.post(`${API_BASE}/sorter/api/keywords/`,
      { keyword_fr: newKeyword },
      { headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${access}` } }
    );
    setNewKeyword('');
    fetchKeywords();
    fetchRejectedData();
  };

  const handleDeleteKeyword = async (id) => {
    if (!user || (!user.is_staff && !user.is_superuser)) return;
    await axios.delete(`${API_BASE}/sorter/api/keywords/${id}/`, {
      headers: { Authorization: `Bearer ${access}` },
    });
    fetchKeywords();
  };

  const handleReFilter = async () => {
    if (!user || (!user.is_staff && !user.is_superuser)) return;
    await axios.post(`${API_BASE}/sorter/api/refilter/`, {}, {
      headers: { Authorization: `Bearer ${access}` },
    });
    fetchRejectedData();
  };

  // --- Effects ---
  useEffect(() => {
    fetchRejectedData();
    fetchKeywords();
    const interval = setInterval(() => fetchRejectedData(), 40 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // --- Columns ---
  const columns = useMemo(() => [
    { accessorKey: 'consultation_id', header: 'ID', size: 80 },
    { accessorKey: 'client', header: 'Client', size: 150 },
    { accessorKey: 'intitule_projet', header: 'Intitulé du projet', size: 500, enableResizing: true },
    { accessorKey: 'date_publication', header: 'Publication', size: 100 },
    { accessorKey: 'date_expiration', header: 'Expiration', size: 100 },
    {
      accessorKey: 'lien',
      header: 'Lien',
      size: 100,
      Cell: ({ cell }) => <a href={cell.getValue()} target="_blank" rel="noopener noreferrer">Lien</a>,
    },
    { accessorKey: 'source', header: 'Source', size: 100 },
    {
      id: 'status',
      header: 'Status',
      size: 100,
      minSize: 80,
      maxSize: 120,
      enableColumnFilter: false,
      enableSorting: false,
      Cell: ({ row }) => (
        <button
          onClick={() => handleFeedback(row.original, 1)}
          style={{
            backgroundColor: '#0077cc',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            padding: '8px 16px',
            cursor: 'pointer',
            fontWeight: '600',
            transition: 'background-color 0.3s ease'
          }}
          onMouseEnter={(e) => e.target.style.backgroundColor = '#005fa3'}
          onMouseLeave={(e) => e.target.style.backgroundColor = '#0077cc'}
        >
          Keep
        </button>
      ),
    },
  ], []);

  return (
    <div className="filtered-container">

      {/* Keywords Drawer Toggle */}
      <button className="keywords-toggle-btn" onClick={() => setIsDrawerOpen(true)}>Keywords</button>

      {isDrawerOpen && (
        <div className="keywords-drawer">
          <button className="close-drawer" onClick={() => setIsDrawerOpen(false)}>❌</button>
          <h2>Keywords</h2>
          {(user?.is_staff || user?.is_superuser) && (
            <>
              <input type="text" value={newKeyword} onChange={(e) => setNewKeyword(e.target.value)} placeholder="New keyword"/>
              <button onClick={handleAddKeyword}>Add</button>
            </>
          )}
          <ul>
            {keywords.map((kw) => (
              <li key={kw.id}>
                {kw.keyword_fr}
                {(user?.is_staff || user?.is_superuser) && <button onClick={() => handleDeleteKeyword(kw.id)}>❌</button>}
              </li>
            ))}
          </ul>
          {(user?.is_staff || user?.is_superuser) && <button className="refilter-btn" onClick={handleReFilter}>Re-filter</button>}
        </div>
      )}

      {/* Table */}
      <div className="table-wrapper">
        <MaterialReactTable
          columns={columns}
          data={data}
          state={{ isLoading }}
          enableColumnResizing
          enableColumnOrdering
          enableDensityToggle
          density="compact"
          enableGlobalFilter
          enablePagination
        />
      </div>
    </div>
  );
}

export default Rejected;
