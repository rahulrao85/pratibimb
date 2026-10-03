import React, { useState } from 'react';
import { ShieldAlert, CheckCircle, AlertTriangle, AlertCircle, HelpCircle, Filter } from 'lucide-react';

export default function HowMeeraDecides({ senior, decisions }) {
  const [filter, setFilter] = useState('all');

  const filteredDecisions = (decisions || []).filter(d => {
    if (filter === 'mistakes') return d.mistake;
    if (filter === 'precedents') return !d.holdout && !d.mistake;
    if (filter === 'holdouts') return d.holdout;
    return true;
  });

  const getDecisionBadge = (decision) => {
    switch (decision) {
      case 'approved':
        return <span className="tag tag-success">Approved</span>;
      case 'approved_with_conditions':
        return <span className="tag tag-warning">Approved w/ Conditions</span>;
      case 'escalated':
        return <span className="tag tag-info">Escalated</span>;
      case 'rejected':
      case 'refuse':
        return <span className="tag tag-danger">Refused</span>;
      default:
        return <span className="tag">{decision}</span>;
    }
  };

  const getOutcomeBadge = (status) => {
    switch (status) {
      case 'good':
        return <span style={{ color: 'var(--success)', fontSize: '0.75rem', fontWeight: 600 }}>● Good Outcome</span>;
      case 'bad':
        return <span style={{ color: 'var(--danger)', fontSize: '0.75rem', fontWeight: 600 }}>● Failed / Bad Outcome</span>;
      case 'mixed':
        return <span style={{ color: 'var(--warning)', fontSize: '0.75rem', fontWeight: 600 }}>● Mixed Outcome</span>;
      default:
        return null;
    }
  };

  // Convert ISO 2025-03-21 to 21-Mar-2025
  const formatDate = (isoStr) => {
    if (!isoStr) return '';
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const parts = isoStr.split('-');
    if (parts.length === 3) {
      const day = parts[2];
      const month = months[parseInt(parts[1], 10) - 1] || parts[1];
      const year = parts[0];
      return `${day}-${month}-${year}`;
    }
    return isoStr;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Senior Profile Summary */}
      <div className="glass-card" style={{ padding: '1.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: 'var(--radius-full)',
                background: 'linear-gradient(135deg, #1e40af, #3b82f6)',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: '1.25rem'
              }}>
                MN
              </div>
              <div>
                <h2 style={{ fontSize: '1.35rem', color: 'var(--text-primary)' }}>
                  {senior ? senior.name : 'Meera Nair'}
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                  {senior ? senior.title : 'Head of Delivery Operations'} · {senior ? senior.org : 'Meridian Global Services'} ({senior ? senior.location : 'Mumbai'})
                </p>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <div style={{ background: 'var(--bg-inset)', padding: '0.5rem 1rem', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem' }}>
              <div style={{ color: 'var(--text-muted)' }}>Signature Limit</div>
              <strong style={{ fontSize: '0.95rem', color: 'var(--primary-color)' }}>₹5,00,000 INR</strong>
            </div>
            <div style={{ background: 'var(--bg-inset)', padding: '0.5rem 1rem', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem' }}>
              <div style={{ color: 'var(--text-muted)' }}>Operational Span</div>
              <strong>180 staff · 14 vendors · 3 accounts</strong>
            </div>
            <div style={{ background: 'var(--bg-inset)', padding: '0.5rem 1rem', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem' }}>
              <div style={{ color: 'var(--text-muted)' }}>Tenure</div>
              <strong>9 years in GCC</strong>
            </div>
          </div>
        </div>

        <p style={{ marginTop: '1.25rem', padding: '0.85rem 1.25rem', background: 'var(--bg-inset)', borderRadius: 'var(--radius-sm)', fontSize: '0.9rem', fontStyle: 'italic', borderLeft: '3px solid var(--primary-color)' }}>
          "{senior?.decision_style?.summary || 'Paper-first, outcomes-driven. Reads the clause, not the email. Rings the requester before signing anything new. Distrusts headline prices and headline guarantees.'}"
        </p>
      </div>

      {/* Decision Style: Principles, Red Flags & Instinct Questions */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        {/* Core Principles */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.05rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--primary-color)' }}>
            ⚖️ Core Decision Principles
          </h3>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            {(senior?.decision_style?.principles || [
              "If it can renew itself, it will — read the renewal clause before the price.",
              "A vendor with 2+ missed SLAs is a process problem, not a relationship problem.",
              "Whoever handles client data must be answerable for where it lives.",
              "The lowest quote is rarely the lowest cost; ask for the fully-loaded number.",
              "Anyone can approve a good deal; the job is catching the deal that looks good."
            ]).map((p, idx) => (
              <li key={idx} style={{ fontSize: '0.85rem', display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                <span style={{ color: 'var(--primary-color)', fontWeight: 700 }}>{idx + 1}.</span>
                <span>{p}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Red Flags */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.05rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--danger)' }}>
            🚩 Red Flags She Looks For
          </h3>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            {(senior?.decision_style?.red_flags || [
              "Auto-renewal / evergreen clauses",
              "No penalty or service-credit for a missed SLA",
              "Advance payment above 30% on a young vendor",
              "Key person named on the contract who has already left",
              "Price increases above 8% without a competing quote",
              "Client data handled without an approved sub-processor list"
            ]).map((f, idx) => (
              <li key={idx} style={{ fontSize: '0.85rem', display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                <span style={{ color: 'var(--danger)' }}>⚠️</span>
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Questions She Always Asks */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.05rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-color)' }}>
            🔍 Instinct Questions She Always Asks
          </h3>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            {(senior?.decision_style?.questions_she_always_asks || [
              "What happened the last time we did this?",
              "What is the worst case if this vendor fails mid-term?",
              "Can we get out in 90 days if we need to?",
              "Who is the named person on this, and are they still there?",
              "Where does the data live, and who else touches it?"
            ]).map((q, idx) => (
              <li key={idx} style={{ fontSize: '0.85rem', display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                <span style={{ color: 'var(--accent-color)' }}>❓</span>
                <span style={{ fontStyle: 'italic' }}>"{q}"</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Past Decisions Ledger (40 Decisions) */}
      <div className="glass-card" style={{ padding: '1.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', color: 'var(--text-primary)' }}>
              Episodic Decision Memory ({filteredDecisions.length} Decisions)
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
              Learnt from 40 historical decisions with real outcomes and the 4 critical mistakes that formed governance lessons.
            </p>
          </div>

          {/* Filter Pills */}
          <div style={{ display: 'flex', gap: '0.4rem', background: 'var(--bg-inset)', padding: '0.25rem', borderRadius: 'var(--radius-sm)' }}>
            <button
              onClick={() => setFilter('all')}
              className="btn"
              style={{
                padding: '0.35rem 0.65rem',
                fontSize: '0.75rem',
                background: filter === 'all' ? 'var(--bg-secondary)' : 'transparent',
                color: filter === 'all' ? 'var(--primary-color)' : 'var(--text-secondary)',
                boxShadow: filter === 'all' ? 'var(--shadow-sm)' : 'none'
              }}
            >
              All (40)
            </button>
            <button
              onClick={() => setFilter('precedents')}
              className="btn"
              style={{
                padding: '0.35rem 0.65rem',
                fontSize: '0.75rem',
                background: filter === 'precedents' ? 'var(--bg-secondary)' : 'transparent',
                color: filter === 'precedents' ? 'var(--primary-color)' : 'var(--text-secondary)',
                boxShadow: filter === 'precedents' ? 'var(--shadow-sm)' : 'none'
              }}
            >
              Precedents (26)
            </button>
            <button
              onClick={() => setFilter('mistakes')}
              className="btn"
              style={{
                padding: '0.35rem 0.65rem',
                fontSize: '0.75rem',
                background: filter === 'mistakes' ? 'var(--bg-secondary)' : 'transparent',
                color: filter === 'mistakes' ? 'var(--danger)' : 'var(--text-secondary)',
                boxShadow: filter === 'mistakes' ? 'var(--shadow-sm)' : 'none',
                fontWeight: 700
              }}
            >
              🚨 The 4 Mistakes (4)
            </button>
            <button
              onClick={() => setFilter('holdouts')}
              className="btn"
              style={{
                padding: '0.35rem 0.65rem',
                fontSize: '0.75rem',
                background: filter === 'holdouts' ? 'var(--bg-secondary)' : 'transparent',
                color: filter === 'holdouts' ? 'var(--info)' : 'var(--text-secondary)',
                boxShadow: filter === 'holdouts' ? 'var(--shadow-sm)' : 'none'
              }}
            >
              Backtest Holdouts (10)
            </button>
          </div>
        </div>

        {/* Decisions List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {filteredDecisions.map(dec => (
            <div
              key={dec.id}
              style={{
                padding: '1rem 1.25rem',
                borderRadius: 'var(--radius-sm)',
                background: dec.mistake ? 'var(--danger-light)' : 'var(--bg-inset)',
                border: dec.mistake ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid var(--border-color)',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <strong style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: dec.mistake ? 'var(--danger)' : 'var(--primary-color)' }}>
                    {dec.id}
                  </strong>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {formatDate(dec.date)}
                  </span>
                  <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                    {dec.vendor_name || dec.vendor_id}
                  </span>
                  {dec.holdout && (
                    <span className="tag tag-info" style={{ fontSize: '0.65rem' }}>
                      Backtest Holdout
                    </span>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                    ₹{dec.value_inr?.toLocaleString('en-IN')}
                  </span>
                  {getDecisionBadge(dec.decision)}
                  {getOutcomeBadge(dec.outcome_status)}
                </div>
              </div>

              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                {dec.decision_note}
              </p>

              {/* Mistake Alert Banner */}
              {dec.mistake && (
                <div style={{
                  padding: '0.65rem 0.85rem',
                  background: 'rgba(239, 68, 68, 0.1)',
                  borderRadius: 'var(--radius-sm)',
                  borderLeft: '3px solid var(--danger)',
                  fontSize: '0.825rem',
                  color: 'var(--danger)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '0.5rem'
                }}>
                  <div>
                    <strong>Historical Mistake:</strong> {dec.mistake_note}
                  </div>
                  {dec.lesson_ids?.length > 0 && (
                    <span className="tag tag-danger">
                      Crystallized into Lesson {dec.lesson_ids.join(', ')}
                    </span>
                  )}
                </div>
              )}

              {/* Normal Outcome note */}
              {!dec.mistake && dec.outcome && (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  <strong>Actual Outcome:</strong> {dec.outcome}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
