import React, { useState } from "react";
import axios from "axios";
import "./Login.css";

function Login({ setUser }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const res = await axios.post("http://localhost:8000/api/token/", {
        username,
        password,
      });
      localStorage.setItem("access", res.data.access);
      localStorage.setItem("refresh", res.data.refresh);

      // Fetch user info
      const userRes = await axios.get("http://localhost:8000/api/user/", {
        headers: { Authorization: `Bearer ${res.data.access}` },
      });
      setUser(userRes.data);
    } catch (err) {
      setError("Invalid credentials");
    }
  };

  return (
    <div className="login-bg">
      <div className="login-container">
        <img src="/Progress_Eng.png" alt="Progress Engineering" className="login-logo" />
        <form onSubmit={handleSubmit} className="login-form">
      <h2>Login</h2>
          {error && <div className="login-error">{error}</div>}
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={e => setUsername(e.target.value)}
        required
            className="login-input"
          /><br />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        required
            className="login-input"
          /><br />
          <button type="submit" className="login-button">Login</button>
    </form>
      </div>
    </div>
  );
}

export default Login;