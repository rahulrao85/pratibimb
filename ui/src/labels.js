// Shared display helpers for every decision pack.

export const verdictLabel = (pack, v = '') => (pack?.verdict_labels?.[v]) || v.replace(/_/g, ' ');

export const firstName = (name = '') => name.split(' ')[0] || 'the senior';

// Indian digit grouping: 4600000 -> ₹46,00,000
export const inr = (n) => '₹' + Number(n || 0).toLocaleString('en-IN');

export const fieldValue = (f, v) => {
  if (v === undefined || v === null || v === '') return '—';
  if (f.type === 'bool') return v ? 'Yes' : 'No';
  if (f.type === 'enum') return String(v).replace(/_/g, ' ');
  if (f.name.endsWith('_pct')) return `${v}%`;
  return String(v);
};

// Mandate rule ids look like M-R1 (Meera), S-R1 (Vikram), F-R1 (Kavya)
export const isRuleId = (c = '') => /^[A-Z]-R\d+$/.test(c);
