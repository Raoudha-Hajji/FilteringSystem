import React, { useEffect, useState, useMemo } from 'react';
import './Filtered.css';
import LoadingScreen from './LoadingScreen';
import axios from 'axios';
import { MaterialReactTable } from 'material-react-table';

const API_BASE = process.env.REACT_APP_API_URL || '';

function Rejected({ user }) {
  const [data, setData] = useState([]);
  const [keywords, setKeywords] = useState([]);
  const [newKeyword, setNewKeyword] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const access = localStorage.getItem('access');

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
      alert(`Feedback sent as ${label === 1 ? 'Keep' : 'Reject'}`);
    } catch (error) {
      console.error("Error sending feedback:", error);
      alert("Failed to send feedback.");
    }
  };

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

  useEffect(() => {
    fetchRejectedData();
    fetchKeywords();
    const interval = setInterval(() => {
      fetchRejectedData();
    }, 40 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const handleAddKeyword = async () => {
    if (!newKeyword.trim()) return;
    if (!user || (!user.is_staff && !user.is_superuser)) return;
    await axios.post(`${API_BASE}/sorter/api/keywords/`,
      { keyword_fr: newKeyword },
      { headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${access}` } }
    );
    setNewKeyword("");
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

  const columns = useMemo(() => [
    { 
      accessorKey: 'consultation_id', 
      header: 'ID Consultation',
      size: 120,
      minSize: 100,
      maxSize: 150
    },
    { 
      accessorKey: 'date_publication', 
      header: 'Date Publication',
      size: 140,
      minSize: 120,
      maxSize: 160
    },
    { 
      accessorKey: 'client', 
      header: 'Client',
      size: 200,
      minSize: 150,
      maxSize: 300
    },
    { 
      accessorKey: 'intitule_projet', 
      header: 'Intitulé du projet',
      size: 400,
      minSize: 300,
      maxSize: 800
    },
    { 
      accessorKey: 'date_expiration', 
      header: 'Date Expiration',
      size: 140,
      minSize: 120,
      maxSize: 160
    },
    {
      accessorKey: 'lien',
      header: 'Lien',
      size: 80,
      minSize: 70,
      maxSize: 100,
      Cell: ({ cell }) => (
        <a href={cell.getValue()} target="_blank" rel="noopener noreferrer">
          Lien
        </a>
      ),
      enableColumnFilter: false,
      enableSorting: false,
    },
    { 
      accessorKey: 'source', 
      header: 'Source',
      size: 120,
      minSize: 100,
      maxSize: 150
    },
    {
      id: 'status',
      header: 'Status',
      size: 150,
      minSize: 130,
      maxSize: 180,
      enableColumnFilter: false,
      enableSorting: false,
      Cell: ({ row }) => (
        <>
          <button
            onClick={() => handleFeedback(row.original, 1)}
            style={{ marginRight: '6px' }}
          >
            Keep
          </button>
          <button onClick={() => handleFeedback(row.original, 0)}>Reject</button>
        </>
      ),
    },
  ], []);

  return (
    <div className="filtered-container">
      {/* Keywords Sidebar */}
      <div className="keywords-sidebar">
        <div className={`keyword-section${user && !user.is_staff && !user.is_superuser ? ' keyword-section-normal' : ''}`}>
          <h2>Keywords</h2>
          {(user && (user.is_staff || user.is_superuser)) && (
            <>
              <input
                type="text"
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                placeholder="New keyword"
              />
              <button onClick={handleAddKeyword}>Add</button>
            </>
          )}
          <ul>
            {keywords.map((kw) => (
              <li key={kw.id}>
                {kw.keyword_fr}
                {(user && (user.is_staff || user.is_superuser)) && (
                  <button onClick={() => handleDeleteKeyword(kw.id)}>❌</button>
                )}
              </li>
            ))}
          </ul>
          {(user && (user.is_staff || user.is_superuser)) && (
            <button className="refilter-btn" onClick={handleReFilter}>
              Re-filter
            </button>
          )}
        </div>
      </div>

      {/* Main Table Area */}
      <div className="main-table-area">
        <MaterialReactTable
          columns={columns}
          data={data}
          state={{ isLoading }}
          enableGlobalFilter
          enablePagination
          enableColumnResizing
          layoutMode="grid"
          initialState={{ pagination: { pageSize: 10 } }}
        />
      </div>
    </div>
  );
}

export default Rejected;
