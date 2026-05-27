import { useMemo } from 'react'
import { Line, Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  TimeScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import 'chartjs-adapter-date-fns'

ChartJS.register(
  TimeScale, LinearScale, PointElement, LineElement, BarElement,
  Title, Tooltip, Legend, Filler
)

/**
 * data: [{日期, [valueKey]: number}, ...]
 * valueKey: 欄位名
 * label: 圖例文字
 * type: 'line' | 'bar' | 'bar-signed' (上漲紅、下跌綠)
 * yAxisOptions: 可選 y 軸額外設定
 */
export default function TimeSeriesChart({
  data,
  valueKey,
  label,
  type = 'line',
  color = '#2563eb',
  zeroLine = false,
  unit = '',
  height = 280,
}) {
  const chartData = useMemo(() => {
    const points = data.map(row => ({ x: row['日期'], y: row[valueKey] })).filter(p => p.y != null)
    if (type === 'bar-signed') {
      return {
        datasets: [{
          label,
          data: points,
          backgroundColor: points.map(p => (p.y >= 0 ? '#dc2626' : '#16a34a')),
          borderColor: 'transparent',
        }],
      }
    }
    return {
      datasets: [{
        label,
        data: points,
        borderColor: color,
        backgroundColor: color + '22',
        borderWidth: 1.5,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.15,
        fill: type === 'line',
      }],
    }
  }, [data, valueKey, label, type, color])

  const options = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      title: { display: true, text: label, font: { size: 14, weight: 'bold' }, color: '#334155' },
      tooltip: {
        callbacks: {
          label: (ctx) => `${ctx.dataset.label}: ${Number(ctx.parsed.y).toLocaleString()} ${unit}`,
        },
      },
    },
    scales: {
      x: {
        type: 'time',
        time: { unit: 'month', displayFormats: { month: 'yyyy-MM', day: 'MM-dd' } },
        grid: { display: false },
        ticks: { color: '#64748b', font: { size: 10 } },
      },
      y: {
        grid: { color: '#e2e8f0' },
        ticks: { color: '#64748b', font: { size: 10 } },
      },
    },
  }), [label, unit])

  const Component = type.startsWith('bar') ? Bar : Line
  return (
    <div className="card" style={{ height }}>
      <Component data={chartData} options={options} />
    </div>
  )
}
