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
      background: 'var(--overlay)',
      backdropFilter: 'blur(8px)',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 'var(--space-6)'
    }}>
      <div 
        className="glass-card" 
        style={{
          width: '100%',
          maxWidth: '780px',
          maxHeight: '90vh',
          overflowY: 'auto',
          padding: 'var(--space-7)',
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

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-2)' }}>
          <span className="tag tag-info">AI Builder Cup 2026 · Future of Work</span>
          <span className="tag tag-success">JAPAC Track</span>
        </div>

        <h2 style={{ fontSize: 'var(--text-2xl)', color: 'var(--text-primary)', marginBottom: 'var(--space-1)' }}>
          Pratibimb (प्रतिबिंब)
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-base)', marginBottom: 'var(--space-6)' }}>
          The reflection and mirror-image of a senior enterprise decision-maker.
        </p>

        {/* Pitch Summary */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-4)', marginBottom: 'var(--space-6)' }}>
          <div style={{ background: 'var(--bg-inset)', padding: 'var(--space-4)', borderRadius: 'var(--radius-sm)' }}>
            <h4 style={{ fontSize: 'var(--text-sm)', marginBottom: 'var(--space-2)', color: 'var(--danger)' }}>The Problem</h4>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              Leaders spend 37% of their time making decisions, and 61% say at least half of that time is used ineffectively (McKinsey survey of 1,259 leaders). Routine approvals queue for one person, and when that person leaves, their judgement leaves too.
            </p>
          </div>

          <div style={{ background: 'var(--bg-inset)', padding: 'var(--space-4)', borderRadius: 'var(--radius-sm)' }}>
            <h4 style={{ fontSize: 'var(--text-sm)', marginBottom: 'var(--space-2)', color: 'var(--primary-color)' }}>The Pratibimb Solution</h4>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              One engine, a Pratibimb for each senior. At one fictional company it learns how Meera (operations: vendors), Vikram (sales: leads) and Kavya (finance: spend exceptions) decide; it recommends a verdict inside each one's limits, reads the documents, asks their questions, and leaves the final call with them.
            </p>
          </div>
        </div>

        {/* Rival Comparison Matrix */}
        <div style={{ marginBottom: 'var(--space-6)' }}>
          <h4 style={{ fontSize: 'var(--text-base)', marginBottom: 'var(--space-3)', color: 'var(--text-primary)' }}>
            Why Pratibimb? (The Org Gaps)
          </h4>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--text-xs)' }}>
              <thead>
                <tr style={{ background: 'var(--bg-inset)', textAlign: 'left' }}>
                  <th style={{ padding: 'var(--space-2)' }}>Capability</th>
                  <th style={{ padding: 'var(--space-2)' }}>Chat Assistants (Gemini/ChatGPT)</th>
                  <th style={{ padding: 'var(--space-2)' }}>Digital Twins (Viven - $35M)</th>
                  <th style={{ padding: 'var(--space-2)', color: 'var(--primary-color)' }}>Pratibimb</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: 'var(--space-2)', fontWeight: 600 }}>Learns how YOUR senior decides</td>
                  <td style={{ padding: 'var(--space-2)' }}>Generic best-practice only</td>
                  <td style={{ padding: 'var(--space-2)' }}>Q&A knowledge retrieval</td>
                  <td style={{ padding: 'var(--space-2)', color: 'var(--primary-color)', fontWeight: 700 }}>✓ 90 past decisions + outcomes across 3 seniors (45 held back to test it)</td>
                </tr>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: 'var(--space-2)', fontWeight: 600 }}>Delegation of Authority limits</td>
                  <td style={{ padding: 'var(--space-2)' }}>No guardrails</td>
                  <td style={{ padding: 'var(--space-2)' }}>No approval limits</td>
                  <td style={{ padding: 'var(--space-2)', color: 'var(--primary-color)', fontWeight: 700 }}>✓ Strict mandate rules (M-R#)</td>
                </tr>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: 'var(--space-2)', fontWeight: 600 }}>Challenges predatory clauses</td>
                  <td style={{ padding: 'var(--space-2)' }}>Only if explicitly asked</td>
                  <td style={{ padding: 'var(--space-2)' }}>No</td>
                  <td style={{ padding: 'var(--space-2)', color: 'var(--primary-color)', fontWeight: 700 }}>✓ Auto-renewal & SLA checks</td>
                </tr>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: 'var(--space-2)', fontWeight: 600 }}>Audit-ready decision file</td>
                  <td style={{ padding: 'var(--space-2)' }}>Chat log</td>
                  <td style={{ padding: 'var(--space-2)' }}>Transcript</td>
                  <td style={{ padding: 'var(--space-2)', color: 'var(--primary-color)', fontWeight: 700 }}>✓ Cites clauses, rules & lessons</td>
                </tr>
                <tr>
                  <td style={{ padding: 'var(--space-2)', fontWeight: 600 }}>Empirical proof of accuracy</td>
                  <td style={{ padding: 'var(--space-2)' }}>None</td>
                  <td style={{ padding: 'var(--space-2)' }}>None</td>
                  <td style={{ padding: 'var(--space-2)', color: 'var(--primary-color)', fontWeight: 700 }}>✓ 44/45 blind back-test across 3 seniors, 0 unsafe approvals (rules alone: 33/45)</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Team & Google Stack */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-4)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--border-color)', fontSize: 'var(--text-xs)' }}>
          <div>
            <strong>Team:</strong> Rahul Rao (Builder) + Dipti CA (Domain Expert) · <strong>Finale:</strong> 04-Dec-2026, Singapore
          </div>
          <div>
            <strong>Stack:</strong> Gemini 3.8 Flash on Vertex AI · FastAPI · Cloud Run · React + Vite
          </div>
        </div>
      </div>
    </div>
  );
}
