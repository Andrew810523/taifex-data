import { fmtInt, fmtDec, fmtPct, deltaClass } from '../utils/format'

function Stat({ label, value, sub, valueClass = '' }) {
  return (
    <div className="card">
      <div className="stat-label">{label}</div>
      <div className={`stat-value mt-1 ${valueClass}`}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
    </div>
  )
}

export default function LatestSummary({ latest }) {
  if (!latest) return null
  const stats = latest.stats || {}
  const opt = latest.options || {}
  const date = stats['日期'] || opt['日期']
  const change = stats['加權指數漲跌']

  return (
    <section className="space-y-3">
      <div className="flex items-end justify-between">
        <h2 className="text-lg font-bold text-slate-700">{date} · 收盤概況</h2>
        <span className="text-xs text-slate-500">資料更新：{latest.updated_at}</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        <Stat
          label="加權指數"
          value={fmtDec(stats['加權指數'])}
          sub={`${fmtDec(change, 2, { sign: true })} (${fmtPct(stats['加權指數漲跌幅(%)'])})`}
          valueClass={deltaClass(change)}
        />
        <Stat
          label="當日高低差"
          value={fmtDec(stats['加權指數當日高低差'])}
        />
        <Stat
          label="融資金額 (億)"
          value={fmtDec(stats['融資金額(億)'])}
          sub={`${fmtDec(stats['融資金額變化量(億)'], 2, { sign: true })} 億`}
          valueClass={deltaClass(stats['融資金額變化量(億)'])}
        />
        <Stat
          label="融券 (交易單位)"
          value={fmtInt(stats['融券(交易單位)'])}
          sub={`${fmtInt(stats['融券單位變化量'], { sign: true })}`}
          valueClass={deltaClass(stats['融券單位變化量'])}
        />
        <Stat
          label="外資現貨買賣超 (億)"
          value={fmtDec(stats['外資現貨買賣超'])}
          valueClass={deltaClass(stats['外資現貨買賣超'])}
        />
        <Stat
          label="外資 (大小台) 期貨未平倉"
          value={fmtDec(stats['外資(大小台)期貨未平倉'])}
          sub={`與前日 ${fmtDec(stats['外資期貨未平倉與前日增減'], 2, { sign: true })} / 與結算 ${fmtDec(stats['外資期貨未平倉與結算比'], 2, { sign: true })}`}
          valueClass={deltaClass(stats['外資(大小台)期貨未平倉'])}
        />
        <Stat
          label="散戶買 / 賣權比"
          value={fmtDec(stats['散戶買/賣權比'], 3)}
        />
        <Stat
          label="微台散戶多空比"
          value={fmtPct(stats['微台散戶多空比'])}
          valueClass={deltaClass(stats['微台散戶多空比'])}
        />
      </div>
    </section>
  )
}
