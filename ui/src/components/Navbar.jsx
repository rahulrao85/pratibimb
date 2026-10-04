import React from 'react';
import { HelpCircle, Brain, ScrollText, Inbox, FileText, Target } from 'lucide-react';
import { firstName } from '../labels.js';

export default function Navbar({ activeTab, setActiveTab, theme, toggleTheme, onOpenPitch, packs = [], packId, onSwitchPack, senior }) {
  const first = firstName(senior?.name);
  const tabs = [
    { id: 'memory', label: `How ${first} Decides`, Icon: Brain },
    { id: 'mandate', label: 'Mandate', Icon: ScrollText },
    { id: 'inbox', label: 'Requests', Icon: Inbox },
    { id: 'record', label: 'Decision File', Icon: FileText },
    { id: 'backtest', label: 'Back-Test', Icon: Target },
  ];

  return (
    <header className="app-header">
      <button
        onClick={() => setActiveTab('inbox')}
        aria-label="Pratibimb home"
        style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', background: 'none', border: 0, padding: 0, cursor: 'pointer', textAlign: 'left', color: 'inherit' }}
      >
        <span style={{
          width: '44px', height: '44px', borderRadius: 'var(--radius-sm)', flexShrink: 0,
          background: 'var(--primary-color)', color: 'var(--primary-contrast)',
          display: 'grid', placeItems: 'center',
          fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: 'var(--text-lg)',
          boxShadow: '0 6px 18px var(--glow)'
        }}>
          प्र
        </span>
        <span>
          <span style={{ display: 'block', fontFamily: 'var(--font-heading)', fontSize: 'var(--text-xl)', fontWeight: 700, letterSpacing: 'var(--tracking-tight)', lineHeight: 1.1 }}>
            Pratibimb
          </span>
          <span style={{ display: 'block', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
            The AI mirror of a senior decision-maker
          </span>
        </span>
      </button>

      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
        <button className="btn btn-secondary" onClick={onOpenPitch} style={{ padding: 'var(--space-2) var(--space-4)' }}>
          <HelpCircle size={16} aria-hidden="true" />
          <span>The Pitch</span>
        </button>
        <button
          className="theme-toggle"
          onClick={toggleTheme}
          role="switch"
          aria-checked={theme === 'dark'}
          aria-label={theme === 'dark' ? 'Switch to Aurora (light)' : 'Switch to Voltage (dark)'}
          title={theme === 'dark' ? 'Voltage · switch to light' : 'Aurora · switch to dark'}
        />
      </div>

      {packs.length > 0 && (
        <div className="senior-switch" role="radiogroup" aria-label="Whose Pratibimb">
          <span className="senior-switch-label">Meridian Global Services · whose Pratibimb?</span>
          <div className="senior-switch-options">
            {packs.map(p => {
              const on = p.id === packId;
              return (
                <button key={p.id} role="radio" aria-checked={on} onClick={() => onSwitchPack(p.id)}
                  className={`senior-option selectable${on ? ' is-selected' : ''}`}>
                  <span className="senior-avatar" aria-hidden="true">{p.senior.split(' ').map(w => w[0]).join('')}</span>
                  <span style={{ minWidth: 0 }}>
                    <span className="senior-name">{p.senior}</span>
                    <span className="senior-role">{p.senior_title} · {p.label}</span>
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      <nav className="nav-tabs" aria-label="Sections">
        {tabs.map(({ id, label, Icon }) => (
          <button
            key={id}
            className={`nav-link${activeTab === id ? ' active' : ''}`}
            aria-current={activeTab === id ? 'page' : undefined}
            onClick={() => setActiveTab(id)}
          >
            <Icon size={15} aria-hidden="true" />
            <span>{label}</span>
          </button>
        ))}
      </nav>
    </header>
  );
}
