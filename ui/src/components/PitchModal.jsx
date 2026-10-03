import React from 'react';
import { X, Award, CheckCircle2, ShieldCheck, Users, Zap } from 'lucide-react';

export default function PitchModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(10, 14, 26, 0.65)',
      backdropFilter: 'blur(8px)',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1.5rem'
    }}>
      <div 
        className="glass-card" 
        style={{
          width: '100%',
          maxWidth: '780px',
          maxHeight: '90vh',
          overflowY: 'auto',
          padding: '2.25rem',
          position: 'relative',
          background: 'var(--bg-secondary)',
          boxShadow: 'var(--modal-shadow)'
        }}
      >
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '1.25rem',
            right: '1.25rem',
            background: 'var(--bg-inset)',
            border: 'none',
            borderRadius: 'var(--radius-full)',
            width: '32px',
            height: '32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            color: 'var(--text-secondary)'
          }}
        >
          <X size={18} />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.5rem' }}>
          <span className="tag tag-info">AI Builder Cup 2026 · Future of Work</span>
          <span className="tag tag-success">JAPAC Track</span>
        </div>

        <h2 style={{ fontSize: '1.6rem', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
          Pratibimb (प्रतिबिंब)
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '1.5rem' }}>
          The reflection and mirror-image of a senior enterprise decision-maker.
        </p>

        {/* Pitch Summary */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ background: 'var(--bg-inset)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
            <h4 style={{ fontSize: '0.9rem', marginBottom: '0.4rem', color: 'var(--danger)' }}>The Problem</h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              Executives spend 37% of their time making decisions. In 1,700+ GCCs, routine requests wait 24 hours for senior approval across timezones. When seniors leave, their judgment is lost.
            </p>
          </div>

          <div style={{ background: 'var(--bg-inset)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
            <h4 style={{ fontSize: '0.9rem', marginBottom: '0.4rem', color: 'var(--primary-color)' }}>The Pratibimb Solution</h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              An AI junior that learns how a senior decides. It approves routine cases inside limits, challenges risky contract traps, asks instinct questions, and leaves the final call with the senior.
            </p>
          </div>
        </div>

        {/* Rival Comparison Matrix */}
        <div style={{ marginBottom: '1.5rem' }}>
          <h4 style={{ fontSize: '0.95rem', marginBottom: '0.65rem', color: 'var(--text-primary)' }}>
            Why Pratibimb? (The Org Gaps)
          </h4>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.775rem' }}>
              <thead>
                <tr style={{ background: 'var(--bg-inset)', textAlign: 'left' }}>
                  <th style={{ padding: '0.5rem' }}>Capability</th>
                  <th style={{ padding: '0.5rem' }}>Chat Assistants (Gemini/ChatGPT)</th>
                  <th style={{ padding: '0.5rem' }}>Digital Twins (Viven - $35M)</th>
                  <th style={{ padding: '0.5rem', color: 'var(--primary-color)' }}>Pratibimb</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '0.5rem', fontWeight: 600 }}>Learns how YOUR senior decides</td>
                  <td style={{ padding: '0.5rem' }}>Generic best-practice only</td>
                  <td style={{ padding: '0.5rem' }}>Q&A knowledge retrieval</td>
                  <td style={{ padding: '0.5rem', color: 'var(--primary-color)', fontWeight: 700 }}>✓ 40 past decisions + outcomes</td>
                </tr>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '0.5rem', fontWeight: 600 }}>Delegation of Authority limits</td>
                  <td style={{ padding: '0.5rem' }}>No guardrails</td>
                  <td style={{ padding: '0.5rem' }}>No approval limits</td>
                  <td style={{ padding: '0.5rem', color: 'var(--primary-color)', fontWeight: 700 }}>✓ Strict mandate rules (M-R#)</td>
                </tr>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '0.5rem', fontWeight: 600 }}>Challenges predatory clauses</td>
                  <td style={{ padding: '0.5rem' }}>Only if explicitly asked</td>
                  <td style={{ padding: '0.5rem' }}>No</td>
                  <td style={{ padding: '0.5rem', color: 'var(--primary-color)', fontWeight: 700 }}>✓ Auto-renewal & SLA checks</td>
                </tr>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '0.5rem', fontWeight: 600 }}>Audit-ready decision file</td>
                  <td style={{ padding: '0.5rem' }}>Chat log</td>
                  <td style={{ padding: '0.5rem' }}>Transcript</td>
                  <td style={{ padding: '0.5rem', color: 'var(--primary-color)', fontWeight: 700 }}>✓ Cites clauses, rules & lessons</td>
                </tr>
                <tr>
                  <td style={{ padding: '0.5rem', fontWeight: 600 }}>Empirical proof of accuracy</td>
                  <td style={{ padding: '0.5rem' }}>None</td>
                  <td style={{ padding: '0.5rem' }}>None</td>
                  <td style={{ padding: '0.5rem', color: 'var(--primary-color)', fontWeight: 700 }}>✓ 10/10 (100%) blind back-test</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Team & Google Stack */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)', fontSize: '0.8rem' }}>
          <div>
            <strong>Team:</strong> Rahul Rao (Builder) + Dipti CA (Domain Expert) · <strong>Finale:</strong> 04-Dec-2026, Singapore
          </div>
          <div>
            <strong>Stack:</strong> Google ADK · Gemini 3.8 Flash · Cloud Run · React + Vite
          </div>
        </div>
      </div>
    </div>
  );
}
