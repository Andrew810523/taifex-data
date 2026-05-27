import { useEffect, useState } from 'react'
import { fetchLatest, fetchStats } from './api/data'
import LatestSummary from './components/LatestSummary'
import TimeSeriesChart from './components/TimeSeriesChart'

const RANGE_OPTIONS = [
  { label: '近 60 日', value: 60 },
  { label: '近 180 日', value: 180 },
  { label: '近 1 年', value: 252 },
  { label: '全部', value: 0 },
]

export default function App() {
  const [latest, setLatest] = useState(null)
  const [stats, setStats] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [range, setRange] = useState(60)

  useEffect(() => {
    Promise.all([fetchLatest(), fetchStats()])
      .then(([l, s]) => {
        setLatest(l)
        setStats(s)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const sliced = range > 0 ? stats.slice(-range) : stats

  return (
    <div className="min-h-screen">
      <header className="bg-slate-900 text-white">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">台股籌碼儀表板</h1>
          <span className="text-xs text-slate-400">資料來源：TWSE / TAIFEX</span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {loading && <div className="text-center text-slate-500 py-20">資料載入中...</div>}
        {error && <div className="card text-bear">資料載入失敗：{error}</div>}

        {!loading && !error && (
          <>
            <LatestSummary latest={latest} />

            <section className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-slate-700">趨勢圖</h2>
                <div className="flex gap-1">
                  {RANGE_OPTIONS.map(opt => (
                    <button
                      key={opt.value}
                      onClick={() => setRange(opt.value)}
                      className={`px-3 py-1 rounded text-xs ${
                        range === opt.value
                          ? 'bg-slate-900 text-white'
                          : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <TimeSeriesChart
                  data={sliced}
                  valueKey="加權指數"
                  label="加權指數"
                  color="#2563eb"
                />
                <TimeSeriesChart
                  data={sliced}
                  valueKey="加權指數漲跌"
                  label="加權指數漲跌 (點)"
                  type="bar-signed"
                />
                <TimeSeriesChart
                  data={sliced}
                  valueKey="外資(大小台)期貨未平倉"
                  label="外資 (大小台) 期貨未平倉"
                  color="#7c3aed"
                />
                <TimeSeriesChart
                  data={sliced}
                  valueKey="外資現貨買賣超"
                  label="外資現貨買賣超 (億)"
                  type="bar-signed"
                />
                <TimeSeriesChart
                  data={sliced}
                  valueKey="散戶買/賣權比"
                  label="散戶 買/賣權比"
                  color="#0891b2"
                />
                <TimeSeriesChart
                  data={sliced}
                  valueKey="微台散戶多空比"
                  label="微台散戶多空比 (%)"
                  type="bar-signed"
                  unit="%"
                />
                <TimeSeriesChart
                  data={sliced}
                  valueKey="融資金額(億)"
                  label="融資金額 (億)"
                  color="#ea580c"
                />
                <TimeSeriesChart
                  data={sliced}
                  valueKey="外資期貨未平倉與結算比"
                  label="外資期貨未平倉 與結算比"
                  color="#db2777"
                />
              </div>
            </section>
          </>
        )}
      </main>

      <footer className="text-center text-xs text-slate-400 py-6">
        Built with Vite + React + Tailwind + Chart.js · 資料每交易日 15:15 / 21:30 自動更新
      </footer>
    </div>
  )
}
