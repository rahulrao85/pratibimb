import React from 'react';
import { Sparkles, Sun, Moon, HelpCircle, ShieldCheck } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, darkMode, toggleDarkMode, onOpenPitch }) {
  const tabs = [
    { id: 'memory', label: '1. How Meera Decides', icon: '🧠' },
    { id: 'mandate', label: '2. Mandate & Limits', icon: '📜' },
    { id: 'inbox', label: '3. Request Inbox', icon: '📥' },
    { id: 'record', label: '4. Decision File & Learning', icon: '📑' },
    { id: 'backtest', label: '5. Back-Test Proof', icon: '🎯' },
  ];

  return (
    <header className="app-header" style={{ marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div 
          onClick={() => setActiveTab('inbox')} 
          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.65rem' }}
        >
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: 'var(--radius-md)',
            background: 'linear-gradient(135deg, var(--primary-color), var(--accent-color))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 700,
            fontSize: '1.2rem',
            boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)'
          }}>
            प्र
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                Pratibimb
              </span>
              <span className="tag tag-info" style={{ fontSize: '0.7rem' }}>
                Gemini 3.8 Flash
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              The Senior Decision Mirror · AI Builder Cup 2026
            </p>
          </div>
        </div>
      </div>

      {/* Navigation tabs */}
      <nav style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap', background: 'var(--bg-inset)', padding: '0.25rem', borderRadius: 'var(--radius-md)' }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.45rem 0.85rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.8rem',
              fontWeight: 600,
              border: 'none',
              cursor: 'pointer',
              transition: 'var(--transition)',
              background: activeTab === tab.id ? 'var(--bg-secondary)' : 'transparent',
              color: activeTab === tab.id ? 'var(--primary-color)' : 'var(--text-secondary)',
              boxShadow: activeTab === tab.id ? 'var(--shadow-sm)' : 'none'
            }}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </nav>

      {/* Right controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <button
          className="btn btn-secondary"
          onClick={onOpenPitch}
          style={{ padding: '0.45rem 0.75rem', fontSize: '0.8rem' }}
          title="Concept Pitch & Architecture"
        >
          <HelpCircle size={16} />
          <span>The Pitch</span>
        </button>

        <button
          className="btn btn-secondary"
          onClick={toggleDarkMode}
          style={{ padding: '0.45rem 0.75rem', fontSize: '0.8rem' }}
          title="Toggle Dark Mode"
        >
          {darkMode ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        <div 
          style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.4rem', 
            fontSize: '0.75rem', 
            background: 'var(--success-light)', 
            color: 'var(--success)', 
            padding: '0.35rem 0.75rem', 
            borderRadius: 'var(--radius-full)',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            fontWeight: 600
          }}
        >
          <ShieldCheck size={14} />
          <span>Meera Nair (Senior)</span>
        </div>
      </div>
    </header>
  );
}
