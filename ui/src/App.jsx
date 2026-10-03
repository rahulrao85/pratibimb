import React, { useState, useEffect } from 'react';

export default function App() {
  const [senior, setSenior] = useState(null);
  const [health, setHealth] = useState(null);
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(err => console.log('API offline or not connected yet:', err));

    fetch('/api/senior')
      .then(res => res.json())
      .then(data => setSenior(data))
      .catch(err => console.log('Senior profile fetch error:', err));
  }, []);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    if (!darkMode) {
      document.body.classList.add('dark-theme');
    } else {
      document.body.classList.remove('dark-theme');
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h1 style={{ fontSize: '1.75rem', color: 'var(--primary-color)' }}>Pratibimb</h1>
            <span className="tag tag-info">AI Builder Cup 2026</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem', fontSize: '0.9rem' }}>
            The AI Mirror of Senior Decision-Making · Future of Work
          </p>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <button className="btn btn-secondary" onClick={toggleDarkMode}>
            {darkMode ? '☀️ Light' : '🌙 Dark'}
          </button>
          <div className="tag tag-success">
            ● Engine Online ({health ? health.model : 'gemini-3.8-flash'})
          </div>
        </div>
      </header>

      <main style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '0.75rem' }}>Decision Senior</h2>
          <p style={{ fontWeight: 600, fontSize: '1.1rem', color: 'var(--text-primary)' }}>
            {senior ? senior.name : 'Meera Nair'}
          </p>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1rem' }}>
            {senior ? senior.title : 'Head of Delivery Operations'} · {senior ? senior.org : 'Meridian Global Services'}
          </p>
          <div style={{ background: 'var(--bg-inset)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem' }}>
            <strong>Signature Limit:</strong> ₹5,00,000 INR<br />
            <strong>Operating Span:</strong> 180 staff · 14 vendors · 3 client accounts
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '0.75rem' }}>Google ADK Agents</h2>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.875rem' }}>
            <li>⚡ <strong>Precedent Agent:</strong> Episodic memory & outcome weighting</li>
            <li>🛡️ <strong>Challenger Agent:</strong> Adversarial contract & clause analysis</li>
            <li>🔍 <strong>Interviewer Agent:</strong> Instinct interrogatories for missing info</li>
            <li>⚖️ <strong>Decider Agent:</strong> Mandate guardrails & citation synthesis</li>
            <li>🔄 <strong>Learner Agent:</strong> Senior override learning loop</li>
          </ul>
        </div>
      </main>
    </div>
  );
}
