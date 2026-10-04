import React, { useEffect, useState } from 'react';
import { Send, ArrowRight, ShieldAlert, FileText, CheckCircle2, AlertTriangle, HelpCircle, Sparkles } from 'lucide-react';

export default function RequestInbox({ requests, onSelectRequest, selectedRequestId, onRunDecision, isAnalyzing }) {
  const [activeTab, setActiveTab] = useState('demo'); // 'demo' | 'custom'

  // Custom request state
  const [customReq, setCustomReq] = useState({
    id: 'REQ-CUSTOM',
    vendor_name: 'Zenith Catering',
    vendor_id: 'V-ZENITH',
    type: 'vendor_renewal',
    value_inr: 420000,
    term_months: 12,
    sla_breaches_12m: 0,
    handles_client_data: false,
    advance_pct: 0,
    price_increase_pct: 10,
    description: 'Annual cafeteria catering renewal. Zenith has raised its per-plate rate by 10%, citing food inflation.'
  });
  const [vendors, setVendors] = useState([]);
  useEffect(() => {
    fetch('/api/vendors').then(r => r.json()).then(d => setVendors(d.vendors || [])).catch(() => {});
  }, []);
  const pickVendor = (id) => {
    const v = vendors.find(x => x.id === id);
    setCustomReq(prev => ({
      ...prev,
      vendor_id: id,
      vendor_name: v ? v.name : '',
      handles_client_data: v ? !!v.handles_client_data : prev.handles_client_data
    }));
  };

  const selected = (requests || []).find(r => r.id === selectedRequestId) || requests?.[0];

  const handleCustomChange = (field, value) => {
    setCustomReq(prev => ({ ...prev, [field]: value }));
  };

  const executeAnalysis = (reqToRun) => {
    // Out-of-scope requests (rating people) have no vendor.
    const vendor_id = reqToRun.type === 'out_of_scope' ? 'OUT_OF_SCOPE' : reqToRun.vendor_id;
    onRunDecision({ ...reqToRun, vendor_id });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-7)' }}>
      {/* Header */}
      <div className="glass-card" style={{ padding: 'var(--space-6)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
          <div>
            <h2 style={{ fontSize: 'var(--text-xl)', color: 'var(--text-primary)' }}>
              Vendor Requests Inbox
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)' }}>
              Select a benchmark demo request or simulate a new vendor submission for Pratibimb's scrutiny.
            </p>
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-2)', background: 'var(--bg-inset)', padding: 'var(--space-1)', borderRadius: 'var(--radius-sm)' }}>
            <button
              onClick={() => setActiveTab('demo')}
              className="btn"
              style={{
                padding: 'var(--space-2) var(--space-3)',
                fontSize: 'var(--text-xs)',
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
                padding: 'var(--space-2) var(--space-3)',
                fontSize: 'var(--text-xs)',
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
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-6)' }}>
          {(requests || []).map((req) => {
            const isSelected = req.id === (selected?.id);

            return (
              <div
                key={req.id}
                onClick={() => onSelectRequest(req.id)}
                className={`glass-card selectable${isSelected ? ' is-selected' : ''}`}
                role="button"
                tabIndex={0}
                aria-pressed={isSelected}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelectRequest(req.id); } }}
                style={{
                  padding: 'var(--space-6)',
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
                    color: 'var(--primary-contrast)',
                    padding: 'var(--space-1) var(--space-3)',
                    fontSize: 'var(--text-xs)',
                    fontWeight: 700,
                    borderBottomLeftRadius: 'var(--radius-sm)',
                    textTransform: 'uppercase'
                  }}>
                    Active Case
                  </div>
                )}

                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--text-muted)' }}>
                    {req.id}
                  </span>
                  <span className={`tag ${req.handles_client_data ? 'tag-warning' : 'tag-info'}`}>
                    {(req.type || '').replace(/_/g, ' ')}{req.handles_client_data ? ' · client data' : ''}
                  </span>
                </div>

                <h3 style={{ fontSize: 'var(--text-lg)', marginBottom: 'var(--space-1)', color: 'var(--text-primary)' }}>
                  {req.vendor_name}
                </h3>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--space-3)' }}>
                  Requested by: {req.requested_by}
                </div>

                <div style={{ background: 'var(--bg-inset)', padding: 'var(--space-3) var(--space-4)', borderRadius: 'var(--radius-sm)', fontSize: 'var(--text-xs)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-2)', marginBottom: 'var(--space-4)' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Annual Value:</span><br />
                    <strong style={{ fontSize: 'var(--text-sm)', color: 'var(--primary-color)' }}>
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

                <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: 'var(--space-5)' }}>
                  {req.description}
                </p>

                <button
                  className={`btn ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ width: '100%', fontSize: 'var(--text-sm)' }}
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
        <div className="glass-card" style={{ padding: 'var(--space-7)' }}>
          <h3 style={{ fontSize: 'var(--text-xl)', marginBottom: 'var(--space-4)' }}>Try your own request</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 'var(--space-4)', marginBottom: 'var(--space-6)' }}>
            <div>
              <label htmlFor="custom-vendor" style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, marginBottom: 'var(--space-1)' }}>Vendor</label>
              <select
                id="custom-vendor"
                value={customReq.vendor_id}
                onChange={(e) => pickVendor(e.target.value)}
                style={{ width: '100%', padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              >
                {vendors.map(v => (
                  <option key={v.id} value={v.id}>{v.name} · {v.relationship_months} months with us</option>
                ))}
                <option value="V-CUSTOM">Another vendor (no history with us)</option>
              </select>
              {customReq.vendor_id === 'V-CUSTOM' && (
                <input
                  type="text"
                  aria-label="Vendor name"
                  placeholder="Vendor name"
                  value={customReq.vendor_name}
                  onChange={(e) => handleCustomChange('vendor_name', e.target.value)}
                  style={{ width: '100%', marginTop: 'var(--space-2)', padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
                />
              )}
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, marginBottom: 'var(--space-1)' }}>Request Type</label>
              <select
                value={customReq.type}
                onChange={(e) => handleCustomChange('type', e.target.value)}
                style={{ width: '100%', padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              >
                <option value="vendor_renewal">Vendor Renewal</option>
                <option value="vendor_onboarding">New Vendor Onboarding</option>
                <option value="one_time_spend">One-Time Spend</option>
                <option value="out_of_scope">Employee Performance Rating (Out of Scope)</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, marginBottom: 'var(--space-1)' }}>Annual Value (INR)</label>
              <input
                type="number"
                value={customReq.value_inr}
                onChange={(e) => handleCustomChange('value_inr', parseInt(e.target.value, 10) || 0)}
                style={{ width: '100%', padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, marginBottom: 'var(--space-1)' }}>SLA Breaches (12m)</label>
              <input
                type="number"
                value={customReq.sla_breaches_12m}
                onChange={(e) => handleCustomChange('sla_breaches_12m', parseInt(e.target.value, 10) || 0)}
                style={{ width: '100%', padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, marginBottom: 'var(--space-1)' }}>Term (Months)</label>
              <input
                type="number"
                value={customReq.term_months}
                onChange={(e) => handleCustomChange('term_months', parseInt(e.target.value, 10) || 12)}
                style={{ width: '100%', padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, marginBottom: 'var(--space-1)' }}>Handles Client Data</label>
              <select
                value={customReq.handles_client_data ? 'true' : 'false'}
                onChange={(e) => handleCustomChange('handles_client_data', e.target.value === 'true')}
                style={{ width: '100%', padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              >
                <option value="false">No</option>
                <option value="true">Yes (Confidential Client Data)</option>
              </select>
            </div>
            <div>
              <label htmlFor="custom-price" style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, marginBottom: 'var(--space-1)' }}>Price Change (%)</label>
              <input
                id="custom-price"
                type="number"
                step="0.5"
                value={customReq.price_increase_pct}
                onChange={(e) => handleCustomChange('price_increase_pct', parseFloat(e.target.value) || 0)}
                style={{ width: '100%', padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              />
            </div>
            <div>
              <label htmlFor="custom-advance" style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, marginBottom: 'var(--space-1)' }}>Advance Payment (%)</label>
              <input
                id="custom-advance"
                type="number"
                value={customReq.advance_pct}
                onChange={(e) => handleCustomChange('advance_pct', parseInt(e.target.value, 10) || 0)}
                style={{ width: '100%', padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              />
            </div>
          </div>

          <div style={{ marginBottom: 'var(--space-6)' }}>
            <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, marginBottom: 'var(--space-1)' }}>Request Description / Business Case</label>
            <textarea
              rows={3}
              value={customReq.description}
              onChange={(e) => handleCustomChange('description', e.target.value)}
              style={{ width: '100%', padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
            />
          </div>

          <button
            className="btn btn-primary"
            onClick={() => executeAnalysis(customReq)}
            disabled={isAnalyzing}
          >
            <Sparkles size={16} />
            <span>{isAnalyzing ? 'Five agents deliberating on Gemini...' : 'Run Pratibimb Multi-Agent Scrutiny'}</span>
          </button>
        </div>
      )}

      {/* Multi-Agent Orchestration Visualizer */}
      {isAnalyzing && (
        <div className="glass-card" style={{ padding: 'var(--space-6)', background: 'var(--primary-light)', border: '1px solid var(--primary-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
            <div className="tag tag-info">Active Multi-Agent Deliberation</div>
            <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600 }}>Gemini 3.8 Flash on Vertex AI</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--space-3)', fontSize: 'var(--text-xs)' }}>
            <div style={{ padding: 'var(--space-3)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
              ⚡ <strong>Precedent Agent:</strong> Querying 30 episodic past decisions...
            </div>
            <div style={{ padding: 'var(--space-3)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
              🛡️ <strong>Challenger Agent:</strong> Cross-examining contract clauses...
            </div>
            <div style={{ padding: 'var(--space-3)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
              🔍 <strong>Interviewer Agent:</strong> Generating Meera's questions...
            </div>
            <div style={{ padding: 'var(--space-3)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
              ⚖️ <strong>Decider Agent:</strong> Evaluating limits & mandatory citations...
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
