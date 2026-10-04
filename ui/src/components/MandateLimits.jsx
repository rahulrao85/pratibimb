import React, { useState } from 'react';
import { ShieldCheck, AlertTriangle, XCircle, CheckCircle2, ChevronRight, Lock } from 'lucide-react';

export default function MandateLimits({ mandate }) {
  const [selectedRule, setSelectedRule] = useState(null);

  const limitsTable = mandate?.limits_table || [
    { case: "Renewal ≤ ₹5L · 0 breaches · 12m+ history", action: "Recommend approve", signoff: "Meera, one-click confirm", tag: "success" },
    { case: "Renewal ≤ ₹5L · 1 breach", action: "Approve only with service credit + 90-day exit", signoff: "Meera, one-click confirm", tag: "warning" },
    { case: "Renewal · 2+ breaches", action: "Escalate (Lesson L01)", signoff: "Meera", tag: "info" },
    { case: "Renewal > ₹5L", action: "Escalate (Above Limit)", signoff: "Meera", tag: "info" },
    { case: "Auto-renewal or term > 12 months", action: "Escalate (Evergreen Trap)", signoff: "Meera", tag: "info" },
    { case: "New vendor onboarding", action: "Escalate (No Precedent)", signoff: "Meera", tag: "info" },
    { case: "Vendor handling client data", action: "Escalate + Data Checklist (L03)", signoff: "Meera + DPO", tag: "info" },
    { case: "Price increase > 8%", action: "Escalate + Competing Quote (L02)", signoff: "Meera", tag: "info" },
    { case: "Advance > 30% to vendor < 2 yrs", action: "Escalate (Cash Guardrail L06)", signoff: "Meera", tag: "info" },
    { case: "One-time spend ≤ ₹50k with precedent", action: "Recommend approve", signoff: "Meera, one-click confirm", tag: "success" },
    { case: "One-time spend > ₹50k, no precedent", action: "Escalate", signoff: "Meera", tag: "info" },
    { case: "Any people-performance appraisal rating", action: "Refuse — Strictly Out of Scope", signoff: "N/A", tag: "danger" }
  ];

  const rules = mandate?.rules || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-7)' }}>
      {/* Header & Mandate Core Axiom */}
      <div className="glass-card" style={{ padding: 'var(--space-6)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
          <div style={{ padding: 'var(--space-2)', background: 'var(--primary-light)', borderRadius: 'var(--radius-sm)', color: 'var(--primary-color)' }}>
            <Lock size={22} />
          </div>
          <div>
            <h2 style={{ fontSize: 'var(--text-xl)', color: 'var(--text-primary)' }}>
              Delegation of Authority (DoA) & Approval Limits
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)' }}>
              Checked in code (agents/mandate.py) · Mandate Ref: {mandate?.id || 'MAN-MEERA-2026'} · Effective 01-Oct-2026
            </p>
          </div>
        </div>

        <div style={{
          background: 'var(--bg-inset)',
          padding: 'var(--space-4) var(--space-5)',
          borderRadius: 'var(--radius-sm)',
          borderLeft: '4px solid var(--primary-color)',
          fontSize: 'var(--text-sm)',
          color: 'var(--text-primary)'
        }}>
          <strong>Core Governance Principle:</strong> Pratibimb may recommend approval <em>only</em> where a rule allows it; every other case goes to Meera with a decision file and a recommendation. <strong>Meera makes every final call, and any escalate or refuse rule overrides an earlier approve.</strong>
        </div>
      </div>

      {/* Decision Limits Matrix */}
      <div className="glass-card" style={{ padding: 'var(--space-6)' }}>
        <h3 style={{ fontSize: 'var(--text-lg)', marginBottom: 'var(--space-5)', color: 'var(--text-primary)' }}>
          Delegation of Authority Limits Matrix
        </h3>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--text-sm)' }}>
            <thead>
              <tr style={{ background: 'var(--bg-inset)', borderBottom: '2px solid var(--border-color)', textAlign: 'left' }}>
                <th style={{ padding: 'var(--space-3) var(--space-4)', fontWeight: 600, color: 'var(--text-secondary)' }}>Operating Scenario</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)', fontWeight: 600, color: 'var(--text-secondary)' }}>Pratibimb Authority</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)', fontWeight: 600, color: 'var(--text-secondary)' }}>Required Signoff</th>
              </tr>
            </thead>
            <tbody>
              {limitsTable.map((row, idx) => (
                <tr
                  key={idx}
                  style={{
                    borderBottom: '1px solid var(--border-color)',
                    background: idx % 2 === 0 ? 'transparent' : 'var(--bg-inset)'
                  }}
                >
                  <td style={{ padding: 'var(--space-3) var(--space-4)', fontWeight: 500 }}>
                    {row.case}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                    <span className={`tag tag-${row.tag || (row.action.includes('approve') ? 'success' : row.action.includes('Refuse') ? 'danger' : 'info')}`}>
                      {row.action}
                    </span>
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-secondary)', fontWeight: 600 }}>
                    {row.signoff}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Rulebook Cards (M-R1 to M-R13) */}
      <div className="glass-card" style={{ padding: 'var(--space-6)' }}>
        <div style={{ marginBottom: 'var(--space-5)' }}>
          <h3 style={{ fontSize: 'var(--text-lg)', color: 'var(--text-primary)' }}>
            Codified Mandate Rules ({rules.length} Rules)
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-xs)' }}>
            Checked in code before Gemini sees the request: they set the floor, and Gemini may only be stricter.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-4)' }}>
          {rules.map((rule) => {
            const isRefuse = rule.then === 'refuse';
            const isEscalate = rule.then === 'escalate';
            const isApprove = rule.then === 'approve' || rule.then === 'approve_with_conditions';

            return (
              <div
                key={rule.id}
                style={{
                  padding: 'var(--space-5)',
                  borderRadius: 'var(--radius-sm)',
                  background: isRefuse ? 'var(--danger-light)' : 'var(--bg-inset)',
                  border: isRefuse ? '1px solid color-mix(in srgb, var(--danger) 35%, transparent)' : '1px solid var(--border-color)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--space-3)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <strong style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)', color: isRefuse ? 'var(--danger)' : 'var(--primary-color)' }}>
                    {rule.id}
                  </strong>
                  <span className={`tag tag-${isRefuse ? 'danger' : isEscalate ? 'info' : 'success'}`}>
                    {rule.then}
                  </span>
                </div>

                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                  <strong>Applies To:</strong> {rule.applies_to}
                </div>

                <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-primary)' }}>
                  {rule.reason}
                </p>

                {/* Conditions / Checklists required */}
                {rule.requires_conditions && (
                  <div style={{ fontSize: 'var(--text-xs)', color: 'var(--warning)', background: 'var(--warning-light)', padding: 'var(--space-2) var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                    <strong>Mandatory Clauses:</strong> {rule.requires_conditions.join(', ')}
                  </div>
                )}
                {rule.requires_checklist && (
                  <div style={{ fontSize: 'var(--text-xs)', color: 'var(--info)', background: 'var(--info-light)', padding: 'var(--space-2) var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                    <strong>Security Checklist:</strong> {rule.requires_checklist.join(', ')}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
