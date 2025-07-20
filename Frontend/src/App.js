// src/App.js
import React, { useState, useEffect, useRef } from 'react';
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import Filtered from './pages/Filtered.js';
import Rejected from './pages/Rejected.js';
import Visualization from './pages/visualization';
import Login from './pages/Login';
import AdminUserManagement from './pages/AdminUserManagement';
import axios from 'axios';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef();
  const navigate = useNavigate();

  // Check for token and fetch user info on mount
  useEffect(() => {
    const access = localStorage.getItem('access');
    if (access && !user) {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      axios.get(`${apiUrl}/api/user/`, {
        headers: { Authorization: `Bearer ${access}` },
      })
        .then(res => setUser(res.data))
        .catch(() => setUser(null));
    }
  }, [user]);

  // Close menu on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    }
    if (menuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    } else {
      document.removeEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [menuOpen]);

  const handleLogout = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    setUser(null);
    setMenuOpen(false);
    navigate('/');
  };

  if (!user) {
    return <Login setUser={setUser} />;
  }

  const profileLetter = user.username ? user.username[0].toUpperCase() : '?';

  // Welcome screen component
  const WelcomeScreen = () => (
    <div className="welcome-screen">
      <img src="/Progress_Eng.png" alt="Progress Engineering" className="welcome-logo" />
      <h1 className="welcome-text">Bienvenue</h1>
    </div>
  );

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="logo-container">
          <img
            src="/Progress_Eng.png"
            alt="Progress Engineering"
            className="logo"
          />
        </div>
        <nav className="navbar">
          <Link to="/filtered" className="nav-button">
            Opportunités Filtrées
          </Link>
          <Link to="/rejected" className="nav-button">
            Opportunités Rejetées
          </Link>
          <Link to="/visualization" className="nav-button">
            Vue des Données
          </Link>
          <div className="profile-menu-container" ref={menuRef}>
            <div
              className="profile-circle"
              onClick={() => setMenuOpen((open) => !open)}
              title={user.username}
            >
              {profileLetter}
            </div>
            {menuOpen && (
              <div className="profile-dropdown">
                {user.is_superuser && (
                  <Link
                    to="/admin-users"
                    className="profile-dropdown-item"
                    onClick={() => setMenuOpen(false)}
                  >
                    User Management
                  </Link>
                )}
                <button className="profile-dropdown-item" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            )}
          </div>
        </nav>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<WelcomeScreen />} />
          <Route path="/filtered" element={<Filtered user={user} />} />
          <Route path="/rejected" element={<Rejected user={user} />} />
          <Route path="/visualization" element={<Visualization />} />
          <Route path="/admin-users" element={user.is_superuser ? <AdminUserManagement user={user} /> : <div style={{padding:32, color:'red'}}>You do not have permission to view this page.</div>} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
