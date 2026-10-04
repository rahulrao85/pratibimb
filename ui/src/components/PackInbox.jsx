import React, { useEffect, useState } from 'react';
import { Sparkles, FileText } from 'lucide-react';
import { fieldValue, firstName, inr } from '../labels.js';

const FIELD_STYLE = {
  width: '100%', padding: 'var(--space-2) var(--space-3)', borderRadius: 'var(--radius-sm)',
  border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)'
};
const LABEL_STYLE = { display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, marginBottom: 'var(--space-1)' };

/** Requests inbox for any decision pack described by data (Vikram's leads, Kavya's spend exceptions, …). */
export default function PackInbox({ pack, senior, requests, selectedRequestId, onSelectRequest, onRunDecision, isAnalyzing }) {
  const [tab, setTab] = useState('demo');
  const [entities, setEntities] = useState([]);
  const [custom, setCustom] = useState(null);
  const first = firstName(senior?.name);
  const fields = pack?.fields || [];

  useEffect(() => {
    setTab('demo');
    fetch(`/api/entities?pack=${pack.id}`).then(r => r.json()).then(d => setEntities(d.entities || [])).catch(() => {});
  }, [pack.id]);

  useEffect(() => {
    const base = (requests || [])[0];
    if (base) setCustom({ ...base, id: 'REQ-CUSTOM', document_id: null, description: '' });
  }, [requests]);

  const set = (k, v) => setCustom(prev => ({ ...prev, [k]: v }));
  const pickEntity = (id) => {
    const e = entities.find(x => x.id === id);
    setCustom(prev => ({ ...prev, entity_id: id, entity_name: e ? e.name : prev.entity_name }));
  };

  const run = (req) => onRunDecision(req);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-7)' }}>
      <div className="glass-card" style={{ padding: 'var(--space-6)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
          <div>
            <h2 style={{ fontSize: 'var(--text-xl)' }}>{pack.label}: requests for {first}</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)' }}>
              {senior?.name}, {senior?.title}. Pick a demo request or try your own; Pratibimb gives the verdict {first} would give.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-1)', background: 'var(--bg-inset)', padding: 'var(--space-1)', borderRadius: 'var(--radius-full)' }}>
            {['demo', 'custom'].map(t => (
              <button key={t} className={`nav-link${tab === t ? ' active' : ''}`} style={{ border: 0, cursor: 'pointer', borderRadius: 'var(--radius-full)' }}
                onClick={() => setTab(t)} aria-pressed={tab === t}>
                {t === 'demo' ? `Demo requests (${(requests || []).length})` : 'Try your own'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {tab === 'demo' ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 320px), 1fr))', gap: 'var(--space-6)' }}>
          {(requests || []).map(req => {
            const selected = req.id === selectedRequestId;
            return (
              <div key={req.id} className={`glass-card selectable${selected ? ' is-selected' : ''}`} role="button" tabIndex={0}
                aria-pressed={selected} onClick={() => onSelectRequest(req.id)}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelectRequest(req.id); } }}
                style={{ padding: 'var(--space-6)', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)', flexWrap: 'wrap' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--text-muted)' }}>{req.id}</span>
                  <span className="tag tag-info">{pack.request_types?.[req.type] || req.type}</span>
                  {req.document_id && <span className="tag tag-accent" title="The Challenger agent reads this document"><FileText size={12} aria-hidden="true" /> {req.document_id}</span>}
                </div>
                <h3 style={{ fontSize: 'var(--text-lg)', marginBottom: 'var(--space-1)' }}>{req.entity_name}</h3>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--space-3)' }}>Requested by: {req.requested_by}</div>
                <div style={{ background: 'var(--bg-inset)', padding: 'var(--space-3) var(--space-4)', borderRadius: 'var(--radius-sm)', fontSize: 'var(--text-xs)',
                  display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-2)', marginBottom: 'var(--space-4)' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>{pack.amount_label}:</span><br />
                    <strong style={{ fontSize: 'var(--text-sm)', color: 'var(--primary-color)' }}>{inr(req.amount_inr)}</strong>
                  </div>
                  {fields.slice(0, 5).map(f => (
                    <div key={f.name}>
                      <span style={{ color: 'var(--text-muted)' }}>{f.label}:</span><br />
                      <strong>{fieldValue(f, req[f.name])}</strong>
                    </div>
                  ))}
                </div>
                <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 'var(--space-5)', flex: 1 }}>{req.description}</p>
                <button className={`btn ${selected ? 'btn-primary' : 'btn-secondary'}`} style={{ width: '100%', fontSize: 'var(--text-sm)' }}
                  disabled={isAnalyzing} onClick={(e) => { e.stopPropagation(); onSelectRequest(req.id); run(req); }}>
                  <Sparkles size={16} aria-hidden="true" />
                  <span>{isAnalyzing && selected ? 'Five agents deliberating…' : `Ask ${first}'s Pratibimb`}</span>
                </button>
              </div>
            );
          })}
        </div>
      ) : custom && (
        <div className="glass-card" style={{ padding: 'var(--space-7)' }}>
          <h3 style={{ fontSize: 'var(--text-xl)', marginBottom: 'var(--space-4)' }}>Try your own request</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 220px), 1fr))', gap: 'var(--space-4)', marginBottom: 'var(--space-6)' }}>
            <div>
              <label htmlFor="pk-entity" style={LABEL_STYLE}>{pack.entity_label}</label>
              <select id="pk-entity" value={custom.entity_id} onChange={(e) => pickEntity(e.target.value)} style={FIELD_STYLE}>
                {entities.map(en => (
                  <option key={en.id} value={en.id}>{en.name}{en.relationship_months > 0 && en.relationship_months < 900 ? ` · ${en.relationship_months} months with us` : ''}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="pk-type" style={LABEL_STYLE}>Request type</label>
              <select id="pk-type" value={custom.type} onChange={(e) => set('type', e.target.value)} style={FIELD_STYLE}>
                {Object.entries(pack.request_types || {}).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="pk-amount" style={LABEL_STYLE}>{pack.amount_label} (₹)</label>
              <input id="pk-amount" type="number" value={custom.amount_inr} onChange={(e) => set('amount_inr', parseInt(e.target.value, 10) || 0)} style={FIELD_STYLE} />
            </div>
            {fields.map(f => (
              <div key={f.name}>
                <label htmlFor={`pk-${f.name}`} style={LABEL_STYLE}>{f.label}</label>
                {f.type === 'bool' ? (
                  <select id={`pk-${f.name}`} value={custom[f.name] ? 'true' : 'false'} onChange={(e) => set(f.name, e.target.value === 'true')} style={FIELD_STYLE}>
                    <option value="true">Yes</option><option value="false">No</option>
                  </select>
                ) : f.type === 'enum' ? (
                  <select id={`pk-${f.name}`} value={custom[f.name] ?? ''} onChange={(e) => set(f.name, e.target.value)} style={FIELD_STYLE}>
                    {f.options.map(o => <option key={o} value={o}>{o.replace(/_/g, ' ')}</option>)}
                  </select>
                ) : (
                  <input id={`pk-${f.name}`} type="number" step={f.type === 'float' ? '0.5' : '1'} value={custom[f.name] ?? 0}
                    onChange={(e) => set(f.name, f.type === 'float' ? (parseFloat(e.target.value) || 0) : (parseInt(e.target.value, 10) || 0))} style={FIELD_STYLE} />
                )}
              </div>
            ))}
          </div>
          <div style={{ marginBottom: 'var(--space-6)' }}>
            <label htmlFor="pk-desc" style={LABEL_STYLE}>What the requester wrote</label>
            <textarea id="pk-desc" rows={3} value={custom.description} onChange={(e) => set('description', e.target.value)}
              placeholder="Describe the request in the requester's words. Put any catch here, the way they would mention it."
              style={FIELD_STYLE} />
          </div>
          <button className="btn btn-primary" disabled={isAnalyzing || !custom.description?.trim()} onClick={() => run(custom)}>
            <Sparkles size={16} aria-hidden="true" />
            <span>{isAnalyzing ? 'Five agents deliberating…' : `Ask ${first}'s Pratibimb`}</span>
          </button>
        </div>
      )}
    </div>
  );
}
