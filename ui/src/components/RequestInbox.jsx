import React, { useState } from 'react';
import { Send, ArrowRight, ShieldAlert, FileText, CheckCircle2, AlertTriangle, HelpCircle, Sparkles } from 'lucide-react';

export default function RequestInbox({ requests, onSelectRequest, selectedRequestId, onRunDecision, isAnalyzing }) {
  const [activeTab, setActiveTab] = useState('demo'); // 'demo' | 'custom'
  
  // Custom request state
  const [customReq, setCustomReq] = useState({
    id: 'REQ-CUSTOM',
    vendor_name: 'Apex Cloud Solutions',
    vendor_id: 'V-CUSTOM',
    type: 'vendor_renewal',
    value_inr: 450000,
    term_months: 12,
    sla_breaches_12m: 1,
    handles_client_data: false,
    advance_pct: 20,
    price_increase_pct: 5.0,
    description: 'Annual cloud compute support renewal with single minor SLA latency incident.'
  });

  const selected = (requests || []).find(r => r.id === selectedRequestId) || requests?.[0];

  const handleCustomChange = (field, value) => {
    setCustomReq(prev => ({ ...prev, [field]: value }));
  };

  const executeAnalysis = (reqToRun) => {
    onRunDecision(reqToRun);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div className="glass-card" style={{ padding: '1.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.35rem', color: 'var(--text-primary)' }}>
              Vendor Requests Inbox
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Select a benchmark demo request or simulate a new vendor submission for Pratibimb's scrutiny.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.4rem', background: 'var(--bg-inset)', padding: '0.25rem', borderRadius: 'var(--radius-sm)' }}>
            <button
              onClick={() => setActiveTab('demo')}
              className="btn"
              style={{
                padding: '0.4rem 0.85rem',
                fontSize: '0.8rem',
                background: activeTab === 'demo' ? 'var(--bg-secondary)' : 'transparent',
                color: activeTab === 'demo' ? 'var(--primary-color)' : 'var(--text-secondary)',
                boxShadow: activeTab === 'demo' ? 'var(--shadow-sm)' : 'none'
              }}
            >
              Benchmark Demos (3)
            </button>
            <button
              onClick={() => setActiveTab('custom')}
              className="btn"
              style={{
                padding: '0.4rem 0.85rem',
                fontSize: '0.8rem',
                background: activeTab === 'custom' ? 'var(--bg-secondary)' : 'transparent',
                color: activeTab === 'custom' ? 'var(--primary-color)' : 'var(--text-secondary)',
                boxShadow: activeTab === 'custom' ? 'var(--shadow-sm)' : 'none'
              }}
            >
              Custom Simulator
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {activeTab === 'demo' ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
          {(requests || []).map((req) => {
            const isSelected = req.id === (selected?.id);
            const isHardCase = req.id === 'REQ-002';
            const isDataCase = req.id === 'REQ-003';

            return (
              <div
                key={req.id}
                onClick={() => onSelectRequest(req.id)}
                className="glass-card"
                style={{
                  padding: '1.5rem',
                  cursor: 'pointer',
                  border: isSelected ? '2px solid var(--primary-color)' : '1px solid var(--border-color)',
                  boxShadow: isSelected ? 'var(--hover-shadow)' : 'var(--card-shadow)',
                  position: 'relative',
                  overflow: 'hidden'
                }}
              >
                {isSelected && (
                  <div style={{
                    position: 'absolute',
                    top: 0,
                    right: 0,
                    background: 'var(--primary-color)',
                    color: '#fff',
                    padding: '0.2rem 0.65rem',
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    borderBottomLeftRadius: 'var(--radius-sm)',
                    textTransform: 'uppercase'
                  }}>
                    Active Case
                  </div>
                )}

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                    {req.id}
                  </span>
                  <span className={`tag ${isHardCase ? 'tag-danger' : isDataCase ? 'tag-warning' : 'tag-success'}`}>
                    {req.expected_verdict.toUpperCase()}
                  </span>
                </div>

                <h3 style={{ fontSize: '1.15rem', marginBottom: '0.25rem', color: 'var(--text-primary)' }}>
                  {req.vendor_name}
                </h3>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                  Requested by: {req.requested_by}
                </div>

                <div style={{ background: 'var(--bg-inset)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '1rem' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Annual Value:</span><br />
                    <strong style={{ fontSize: '0.9rem', color: 'var(--primary-color)' }}>
                      ₹{req.value_inr?.toLocaleString('en-IN')}
                    </strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>SLA Breaches:</span><br />
                    <strong style={{ color: req.sla_breaches_12m > 0 ? 'var(--danger)' : 'var(--success)' }}>
                      {req.sla_breaches_12m} breaches
                    </strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Proposed Term:</span><br />
                    <strong>{req.term_months} months</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Client Data:</span><br />
                    <strong>{req.handles_client_data ? '⚠️ Yes' : 'No'}</strong>
                  </div>
                </div>

                <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: '1.25rem' }}>
                  {req.description}
                </p>

                <button
                  className={`btn ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ width: '100%', fontSize: '0.85rem' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectRequest(req.id);
                    executeAnalysis(req);
                  }}
                  disabled={isAnalyzing}
                >
                  <Sparkles size={16} />
                  <span>{isAnalyzing && isSelected ? 'Analyzing with 5 Agents...' : 'Run Pratibimb Scrutiny'}</span>
                </button>
              </div>
            );
          })}
        </div>
      ) : (
        /* Custom Simulator Form */
        <div className="glass-card" style={{ padding: '2rem' }}>
          <h3 style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>Simulate New Vendor Request</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.35rem' }}>Vendor Name</label>
              <input
                type="text"
                value={customReq.vendor_name}
                onChange={(e) => handleCustomChange('vendor_name', e.target.value)}
                style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.35rem' }}>Request Type</label>
              <select
                value={customReq.type}
                onChange={(e) => handleCustomChange('type', e.target.value)}
                style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              >
                <option value="vendor_renewal">Vendor Renewal</option>
                <option value="vendor_onboarding">New Vendor Onboarding</option>
                <option value="one_time_spend">One-Time Spend</option>
                <option value="out_of_scope">Employee Performance Rating (Out of Scope)</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.35rem' }}>Annual Value (INR)</label>
              <input
                type="number"
                value={customReq.value_inr}
                onChange={(e) => handleCustomChange('value_inr', parseInt(e.target.value, 10) || 0)}
                style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.35rem' }}>SLA Breaches (12m)</label>
              <input
                type="number"
                value={customReq.sla_breaches_12m}
                onChange={(e) => handleCustomChange('sla_breaches_12m', parseInt(e.target.value, 10) || 0)}
                style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.35rem' }}>Term (Months)</label>
              <input
                type="number"
                value={customReq.term_months}
                onChange={(e) => handleCustomChange('term_months', parseInt(e.target.value, 10) || 12)}
                style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.35rem' }}>Handles Client Data</label>
              <select
                value={customReq.handles_client_data ? 'true' : 'false'}
                onChange={(e) => handleCustomChange('handles_client_data', e.target.value === 'true')}
                style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              >
                <option value="false">No</option>
                <option value="true">Yes (Confidential Client Data)</option>
              </select>
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.35rem' }}>Request Description / Business Case</label>
            <textarea
              rows={3}
              value={customReq.description}
              onChange={(e) => handleCustomChange('description', e.target.value)}
              style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
            />
          </div>

          <button
            className="btn btn-primary"
            onClick={() => executeAnalysis(customReq)}
            disabled={isAnalyzing}
          >
            <Sparkles size={16} />
            <span>{isAnalyzing ? 'Deliberating across 5 ADK Agents...' : 'Run Pratibimb Multi-Agent Scrutiny'}</span>
          </button>
        </div>
      )}

      {/* Multi-Agent Orchestration Visualizer */}
      {isAnalyzing && (
        <div className="glass-card" style={{ padding: '1.5rem', background: 'var(--primary-light)', border: '1px solid var(--primary-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <div className="tag tag-info">Active Multi-Agent Deliberation</div>
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Google ADK (gemini-3.8-flash)</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem', fontSize: '0.8rem' }}>
            <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
              ⚡ <strong>Precedent Agent:</strong> Querying 30 episodic past decisions...
            </div>
            <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
              🛡️ <strong>Challenger Agent:</strong> Cross-examining contract clauses...
            </div>
            <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
              🔍 <strong>Interviewer Agent:</strong> Generating Meera's instinct questions...
            </div>
            <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
              ⚖️ <strong>Decider Agent:</strong> Evaluating limits & mandatory citations...
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
