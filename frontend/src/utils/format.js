// 數字格式化工具

export function fmtInt(v, { sign = false } = {}) {
  if (v == null || Number.isNaN(v)) return '—'
  const n = Math.round(Number(v))
  const formatted = n.toLocaleString('en-US')
  return sign && n > 0 ? `+${formatted}` : formatted
}

export function fmtDec(v, digits = 2, { sign = false } = {}) {
  if (v == null || Number.isNaN(v)) return '—'
  const n = Number(v)
  const formatted = n.toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
  return sign && n > 0 ? `+${formatted}` : formatted
}

export function fmtPct(v, digits = 2) {
  if (v == null || Number.isNaN(v)) return '—'
  return `${Number(v).toFixed(digits)}%`
}

export function deltaClass(v) {
  if (v == null || Number.isNaN(v)) return ''
  const n = Number(v)
  if (n > 0) return 'stat-delta-up'
  if (n < 0) return 'stat-delta-down'
  return ''
}

export function lastN(arr, n) {
  if (!Array.isArray(arr)) return []
  return arr.slice(-n)
}
