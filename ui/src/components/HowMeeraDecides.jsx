import React, { useState } from 'react';
import { ShieldAlert, CheckCircle, AlertTriangle, AlertCircle, HelpCircle, Filter } from 'lucide-react';

export default function HowMeeraDecides({ senior, decisions, pack }) {
  const first = (senior?.name || 'Meera Nair').split(' ')[0];
  const [filter, setFilter] = useState('all');
  const isOverride = (d) => (d.id || '').startsWith('OVR-');
  const overrideCount = (decisions || []).filter(isOverride).length;

  const filteredDecisions = (decisions || []).filter(d => {
    if (filter === 'mistakes') return d.mistake;
    if (filter === 'precedents') return !d.mistake && !isOverride(d);
    if (filter === 'overrides') return isOverride(d);
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
        return <span style={{ color: 'var(--success)', fontSize: 'var(--text-xs)', fontWeight: 600 }}>● Good Outcome</span>;
      case 'bad':
        return <span style={{ color: 'var(--danger)', fontSize: 'var(--text-xs)', fontWeight: 600 }}>● Failed / Bad Outcome</span>;
      case 'mixed':
        return <span style={{ color: 'var(--warning)', fontSize: 'var(--text-xs)', fontWeight: 600 }}>● Mixed Outcome</span>;
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-7)' }}>
      {/* Senior Profile Summary */}
      <div className="glass-card" style={{ padding: 'var(--space-6)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: 'var(--radius-full)',
                background: 'var(--primary-color)',
                color: 'var(--primary-contrast)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: 'var(--text-xl)'
              }}>
                MN
              </div>
              <div>
                <h2 style={{ fontSize: 'var(--text-xl)', color: 'var(--text-primary)' }}>
                  {senior ? senior.name : ''}
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)' }}>
                  {senior ? senior.title : 'Head of Delivery Operations'} · {senior ? senior.org : 'Meridian Global Services'} ({senior ? senior.location : 'Mumbai'})
                </p>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
            <div style={{ background: 'var(--bg-inset)', padding: 'var(--space-2) var(--space-4)', borderRadius: 'var(--radius-sm)', fontSize: 'var(--text-xs)' }}>
              <div style={{ color: 'var(--text-muted)' }}>Signature Limit</div>
              <strong style={{ fontSize: 'var(--text-base)', color: 'var(--primary-color)' }}>₹5,00,000 INR</strong>
            </div>
            <div style={{ background: 'var(--bg-inset)', padding: 'var(--space-2) var(--space-4)', borderRadius: 'var(--radius-sm)', fontSize: 'var(--text-xs)' }}>
              <div style={{ color: 'var(--text-muted)' }}>Operational Span</div>
              <strong>180 staff · 14 vendors · 3 accounts</strong>
            </div>
            <div style={{ background: 'var(--bg-inset)', padding: 'var(--space-2) var(--space-4)', borderRadius: 'var(--radius-sm)', fontSize: 'var(--text-xs)' }}>
              <div style={{ color: 'var(--text-muted)' }}>Tenure</div>
              <strong>9 years in GCC</strong>
            </div>
          </div>
        </div>

        <p style={{ marginTop: 'var(--space-5)', padding: 'var(--space-3) var(--space-5)', background: 'var(--bg-inset)', borderRadius: 'var(--radius-sm)', fontSize: 'var(--text-sm)', fontStyle: 'italic', borderLeft: '3px solid var(--primary-color)' }}>
          "{senior?.decision_style?.summary || 'Paper-first, outcomes-driven. Reads the clause, not the email. Rings the requester before signing anything new. Distrusts headline prices and headline guarantees.'}"
        </p>
      </div>

      {/* Decision Style: Principles, Red Flags & Instinct Questions */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-6)' }}>
        {/* Core Principles */}
        <div className="glass-card" style={{ padding: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 'var(--text-base)', marginBottom: 'var(--space-4)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: 'var(--primary-color)' }}>
            ⚖️ Core Decision Principles
          </h3>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {(senior?.decision_style?.principles || [
              "If it can renew itself, it will — read the renewal clause before the price.",
              "A vendor with 2+ missed SLAs is a process problem, not a relationship problem.",
              "Whoever handles client data must be answerable for where it lives.",
              "The lowest quote is rarely the lowest cost; ask for the fully-loaded number.",
              "Anyone can approve a good deal; the job is catching the deal that looks good."
            ]).map((p, idx) => (
              <li key={idx} style={{ fontSize: 'var(--text-sm)', display: 'flex', gap: 'var(--space-2)', alignItems: 'flex-start' }}>
                <span style={{ color: 'var(--primary-color)', fontWeight: 700 }}>{idx + 1}.</span>
                <span>{p}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Red Flags */}
        <div className="glass-card" style={{ padding: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 'var(--text-base)', marginBottom: 'var(--space-4)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: 'var(--danger)' }}>
            🚩 Red Flags She Looks For
          </h3>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {(senior?.decision_style?.red_flags || [
              "Auto-renewal / evergreen clauses",
              "No penalty or service-credit for a missed SLA",
              "Advance payment above 30% on a young vendor",
              "Key person named on the contract who has already left",
              "Price increases above 8% without a competing quote",
              "Client data handled without an approved sub-processor list"
            ]).map((f, idx) => (
              <li key={idx} style={{ fontSize: 'var(--text-sm)', display: 'flex', gap: 'var(--space-2)', alignItems: 'flex-start' }}>
                <span style={{ color: 'var(--danger)' }}>⚠️</span>
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Questions She Always Asks */}
        <div className="glass-card" style={{ padding: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 'var(--text-base)', marginBottom: 'var(--space-4)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: 'var(--accent-color)' }}>
            🔍 Instinct Questions She Always Asks
          </h3>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {(senior?.decision_style?.questions_she_always_asks || [
              "What happened the last time we did this?",
              "What is the worst case if this vendor fails mid-term?",
              "Can we get out in 90 days if we need to?",
              "Who is the named person on this, and are they still there?",
              "Where does the data live, and who else touches it?"
            ]).map((q, idx) => (
              <li key={idx} style={{ fontSize: 'var(--text-sm)', display: 'flex', gap: 'var(--space-2)', alignItems: 'flex-start' }}>
                <span style={{ color: 'var(--accent-color)' }}>❓</span>
                <span style={{ fontStyle: 'italic' }}>"{q}"</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Past Decisions Ledger (30 in memory + overrides) */}
      <div className="glass-card" style={{ padding: 'var(--space-6)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-4)', marginBottom: 'var(--space-5)' }}>
          <div>
            <h3 style={{ fontSize: 'var(--text-lg)', color: 'var(--text-primary)' }}>
              Decision Memory ({filteredDecisions.length} shown)
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-xs)' }}>
              Learns from 30 past decisions with real outcomes, including the 4 mistakes that became lessons. 15 more are held back for the blind back-test.
            </p>
          </div>

          {/* Filter Pills */}
          <div style={{ display: 'flex', gap: 'var(--space-2)', background: 'var(--bg-inset)', padding: 'var(--space-1)', borderRadius: 'var(--radius-sm)' }}>
            <button
              onClick={() => setFilter('all')}
              className="btn"
              style={{
                padding: 'var(--space-1) var(--space-3)',
                fontSize: 'var(--text-xs)',
                background: filter === 'all' ? 'var(--bg-secondary)' : 'transparent',
                color: filter === 'all' ? 'var(--primary-color)' : 'var(--text-secondary)',
                boxShadow: filter === 'all' ? 'var(--shadow-sm)' : 'none'
              }}
            >
              All ({(decisions || []).length})
            </button>
            <button
              onClick={() => setFilter('precedents')}
              className="btn"
              style={{
                padding: 'var(--space-1) var(--space-3)',
                fontSize: 'var(--text-xs)',
                background: filter === 'precedents' ? 'var(--bg-secondary)' : 'transparent',
                color: filter === 'precedents' ? 'var(--primary-color)' : 'var(--text-secondary)',
                boxShadow: filter === 'precedents' ? 'var(--shadow-sm)' : 'none'
              }}
            >
              Precedents ({(decisions || []).filter(d => !d.mistake && !isOverride(d)).length})
            </button>
            <button
              onClick={() => setFilter('mistakes')}
              className="btn"
              style={{
                padding: 'var(--space-1) var(--space-3)',
                fontSize: 'var(--text-xs)',
                background: filter === 'mistakes' ? 'var(--bg-secondary)' : 'transparent',
                color: filter === 'mistakes' ? 'var(--danger)' : 'var(--text-secondary)',
                boxShadow: filter === 'mistakes' ? 'var(--shadow-sm)' : 'none',
                fontWeight: 700
              }}
            >
              🚨 Mistakes ({(decisions || []).filter(d => d.mistake).length})
            </button>
            <button
              onClick={() => setFilter('overrides')}
              className="btn"
              style={{
                padding: 'var(--space-1) var(--space-3)',
                fontSize: 'var(--text-xs)',
                background: filter === 'overrides' ? 'var(--bg-secondary)' : 'transparent',
                color: filter === 'overrides' ? 'var(--info)' : 'var(--text-secondary)',
                boxShadow: filter === 'overrides' ? 'var(--shadow-sm)' : 'none'
              }}
            >
              {first}'s overrides ({overrideCount})
            </button>
          </div>
        </div>

        {/* Decisions List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {filteredDecisions.map(dec => (
            <div
              key={dec.id}
              style={{
                padding: 'var(--space-4) var(--space-5)',
                borderRadius: 'var(--radius-sm)',
                background: dec.mistake ? 'var(--danger-light)' : 'var(--bg-inset)',
                border: dec.mistake ? '1px solid color-mix(in srgb, var(--danger) 35%, transparent)' : '1px solid var(--border-color)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-2)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                  <strong style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)', color: dec.mistake ? 'var(--danger)' : 'var(--primary-color)' }}>
                    {dec.id}
                  </strong>
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                    {formatDate(dec.date)}
                  </span>
                  <span style={{ fontWeight: 600, fontSize: 'var(--text-sm)' }}>
                    {dec.vendor_name || dec.entity_name || dec.vendor_id}
                  </span>
                  {isOverride(dec) && (
                    <span className="tag tag-warning" style={{ fontSize: 'var(--text-xs)' }}>
                      {first}'s override
                    </span>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600 }}>
                    ₹{(dec.value_inr ?? dec.amount_inr)?.toLocaleString('en-IN')}
                  </span>
                  {getDecisionBadge(dec.decision)}
                  {getOutcomeBadge(dec.outcome_status)}
                </div>
              </div>

              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>
                {dec.decision_note}
              </p>

              {/* Mistake Alert Banner */}
              {dec.mistake && (
                <div style={{
                  padding: 'var(--space-3) var(--space-3)',
                  background: 'var(--danger-light)',
                  borderRadius: 'var(--radius-sm)',
                  borderLeft: '3px solid var(--danger)',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--danger)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: 'var(--space-2)'
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
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
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
