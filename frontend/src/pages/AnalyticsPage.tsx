import { useEffect, useMemo, useState } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { motion, AnimatePresence } from "framer-motion";
import { BarChart3, Download, Cpu, Route as RouteIcon, Waypoints } from "lucide-react";
import jsPDF from "jspdf";
import {
  generateDaily,
  generateWeekly,
  generateMonthly,
  generateYearly,
  summarize,
  type AnalyticsPoint,
} from "../lib/analyticsData";
import { mlApi, routeHistoryApi } from "../lib/api";
import type { MLStatus, RouteHistoryEntry } from "../lib/types";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler);

type ViewMode = "Daily" | "Weekly" | "Monthly" | "Yearly";

function isoDate(d: Date) {
  return d.toISOString().slice(0, 10);
}

function startOfWeek(d: Date) {
  const date = new Date(d);
  const day = date.getDay();
  const diff = (day === 0 ? -6 : 1) - day; // back up to Monday
  date.setDate(date.getDate() + diff);
  return date;
}

export default function AnalyticsPage() {
  const [mode, setMode] = useState<ViewMode>("Daily");
  const [dateStr, setDateStr] = useState(isoDate(new Date()));
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());

  const [ml, setMl] = useState<MLStatus | null>(null);
  const [history, setHistory] = useState<RouteHistoryEntry[]>([]);

  useEffect(() => {
    mlApi.status().then(setMl).catch(() => {});
    routeHistoryApi.list(20).then(setHistory).catch(() => {});
  }, []);

  const points: AnalyticsPoint[] = useMemo(() => {
    if (mode === "Daily") return generateDaily(dateStr);
    if (mode === "Weekly") return generateWeekly(isoDate(startOfWeek(new Date(dateStr))));
    if (mode === "Monthly") return generateMonthly(month, year);
    return generateYearly();
  }, [mode, dateStr, month, year]);

  const summary = useMemo(() => summarize(points), [points]);

  const chartData = {
    labels: points.map((p) => p.label),
    datasets: [
      {
        label: "Deliveries",
        data: points.map((p) => p.deliveries),
        borderColor: "#3ee6c4",
        backgroundColor: "rgba(62,230,196,0.12)",
        fill: true,
        tension: 0.35,
        pointRadius: mode === "Monthly" ? 0 : 3,
        yAxisID: "y",
      },
      {
        label: "Avg ETA (min)",
        data: points.map((p) => p.avgEtaMinutes),
        borderColor: "#5ec8f5",
        backgroundColor: "transparent",
        tension: 0.35,
        pointRadius: 0,
        borderDash: [4, 3],
        yAxisID: "y1",
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 500, easing: "easeOutQuart" as const },
    interaction: { mode: "index" as const, intersect: false },
    plugins: {
      legend: { labels: { color: "#9fb0c9", font: { family: "Inter", size: 11 } } },
      tooltip: {
        backgroundColor: "#111826",
        borderColor: "#22304a",
        borderWidth: 1,
        titleColor: "#e7edf5",
        bodyColor: "#9fb0c9",
        callbacks: {
          afterBody: (items: any[]) => {
            const p = points[items[0].dataIndex];
            return [`Fuel efficiency: ${p.fuelEfficiencyPct}%`, `Delay: ${p.delayPct}%`];
          },
        },
      },
    },
    scales: {
      x: { ticks: { color: "#5b6b85", font: { family: "JetBrains Mono", size: 10 } }, grid: { color: "#1b2434" } },
      y: {
        position: "left" as const,
        ticks: { color: "#5b6b85", font: { size: 10 } },
        grid: { color: "#1b2434" },
        title: { display: true, text: "Deliveries", color: "#5b6b85", font: { size: 10 } },
      },
      y1: {
        position: "right" as const,
        ticks: { color: "#5b6b85", font: { size: 10 } },
        grid: { display: false },
        title: { display: true, text: "ETA (min)", color: "#5b6b85", font: { size: 10 } },
      },
    },
  };

  function handleDownloadReport() {
    const doc = new jsPDF();
    let y = 18;
    doc.setFontSize(16);
    doc.text("RouteXAI Analysis Report", 14, y);
    y += 8;
    doc.setFontSize(10);
    doc.setTextColor(100);
    const rangeLabel =
      mode === "Daily"
        ? dateStr
        : mode === "Weekly"
        ? `Week of ${isoDate(startOfWeek(new Date(dateStr)))}`
        : mode === "Monthly"
        ? `${month}/${year}`
        : "Last 5 years";
    doc.text(`Mode: ${mode}   Range: ${rangeLabel}`, 14, y);
    y += 10;

    doc.setTextColor(20);
    doc.setFontSize(12);
    doc.text("Summary", 14, y);
    y += 6;
    doc.setFontSize(10);
    doc.text(`Total Deliveries: ${summary.totalDeliveries}`, 14, y);
    y += 5;
    doc.text(`Average ETA (ML Predicted): ${summary.avgEtaMinutes} min`, 14, y);
    y += 5;
    doc.text(`On-Time Delivery: ${summary.onTimePct}%`, 14, y);
    y += 5;
    doc.text(`Traffic Impact Index: ${summary.trafficImpactIndex}`, 14, y);
    y += 10;

    doc.setFontSize(12);
    doc.text("ML Insights", 14, y);
    y += 6;
    doc.setFontSize(10);
    doc.text(`Optimization Engine: ${ml?.optimization_engine ?? "Google OR-Tools (VRPTW)"}`, 14, y);
    y += 5;
    doc.text(`Shortest Path Algorithm: ${ml?.shortest_path_algorithm ?? "A* Search"}`, 14, y);
    y += 5;
    doc.text(`ETA Prediction Model: ${ml?.eta_prediction_model ?? "Supervised Regression"}`, 14, y);
    y += 5;
    doc.text(`Model Trained: ${ml?.model_trained ? "Yes" : "No (heuristic fallback)"}`, 14, y);
    y += 10;

    doc.setFontSize(12);
    doc.text(`${mode} Breakdown (first 15 rows)`, 14, y);
    y += 6;
    doc.setFontSize(8);
    points.slice(0, 15).forEach((p) => {
      doc.text(
        `${p.label}   deliveries=${p.deliveries}  eta=${p.avgEtaMinutes}min  fuel=${p.fuelEfficiencyPct}%  delay=${p.delayPct}%`,
        14,
        y
      );
      y += 4.2;
    });

    doc.setFontSize(7);
    doc.setTextColor(150);
    doc.text(
      "Chart data in this report is simulated for demonstration; ML Insights reflect the live model.",
      14,
      285
    );

    doc.save(`routexai-${mode.toLowerCase()}-report-${rangeLabel.replace(/[\s/]/g, "-")}.pdf`);
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-xl text-ink flex items-center gap-2">
            <BarChart3 size={18} className="text-signal" /> Analysis
          </h1>
          <p className="text-sm text-ink-faint mt-1">Delivery performance trends across time.</p>
        </div>
        <button
          onClick={handleDownloadReport}
          className="flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg bg-signal/15 border border-signal/40 text-signal hover:bg-signal/25 transition-colors"
        >
          <Download size={15} /> Download Report
        </button>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        {(["Daily", "Weekly", "Monthly", "Yearly"] as ViewMode[]).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              mode === m ? "bg-signal/15 border-signal/40 text-signal" : "border-panelBorder text-ink-faint hover:text-ink"
            }`}
          >
            {m} Analysis
          </button>
        ))}

        {(mode === "Daily" || mode === "Weekly") && (
          <input
            type="date"
            value={dateStr}
            onChange={(e) => setDateStr(e.target.value)}
            className="input w-auto ml-2"
          />
        )}
        {mode === "Monthly" && (
          <div className="flex items-center gap-2 ml-2">
            <select value={month} onChange={(e) => setMonth(Number(e.target.value))} className="input w-auto">
              {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                <option key={m} value={m}>
                  {new Date(2000, m - 1, 1).toLocaleString("en", { month: "long" })}
                </option>
              ))}
            </select>
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              className="input w-24"
            />
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SummaryCard label="Total Deliveries" value={String(summary.totalDeliveries)} />
        <SummaryCard label="Avg ETA (ML Predicted)" value={`${summary.avgEtaMinutes} min`} />
        <SummaryCard label="On-Time Delivery %" value={`${summary.onTimePct}%`} accent="status-success" />
        <SummaryCard label="Traffic Impact Index" value={String(summary.trafficImpactIndex)} accent="status-warn" />
      </div>

      <div className="panel p-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={mode + dateStr + month + year}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            style={{ height: 340 }}
          >
            <Line data={chartData} options={chartOptions as any} />
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="panel p-4">
          <h2 className="font-display text-sm text-ink mb-3 flex items-center gap-2">
            <Cpu size={14} className="text-signal" /> ML Insights
          </h2>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <InsightRow icon={<RouteIcon size={13} />} label="Optimization Engine" value={ml?.optimization_engine ?? "—"} />
            <InsightRow icon={<Waypoints size={13} />} label="Shortest Path" value={ml?.shortest_path_algorithm ?? "—"} />
            <InsightRow icon={<Cpu size={13} />} label="ETA Model" value={ml?.eta_prediction_model ?? "—"} />
            <InsightRow
              label="Model Confidence"
              value={
                (ml?.metadata as any)?.confidence_percentage
                  ? `${(ml?.metadata as any).confidence_percentage}%`
                  : "Heuristic fallback"
              }
            />
          </div>
        </div>

        <div className="panel p-4">
          <h2 className="font-display text-sm text-ink mb-3">Predicted vs Actual ETA (recent deliveries)</h2>
          <div className="space-y-1.5 max-h-40 overflow-y-auto">
            {history.slice(0, 6).map((h) => (
              <div key={h.id} className="flex items-center justify-between text-xs">
                <span className="text-ink-faint font-mono">Vehicle #{h.vehicle_id}</span>
                <span className="text-ink-dim">
                  {h.eta_predicted?.toFixed(0) ?? "—"} → {h.eta_actual?.toFixed(0) ?? "—"} min
                </span>
                <span className={h.delay > 10 ? "text-status-danger" : "text-status-success"}>
                  {h.delay > 10 ? "Delayed" : "On track"}
                </span>
              </div>
            ))}
            {history.length === 0 && <p className="text-xs text-ink-faint">No route history yet.</p>}
          </div>
        </div>
      </div>

      <p className="text-xs text-ink-faint">
        Chart and summary data on this page are simulated for demonstration (per design, no live backend
        aggregation is required here); ML Insights and Predicted vs Actual ETA reflect the real trained model
        and route history.
      </p>
    </div>
  );
}

function SummaryCard({ label, value, accent = "signal" }: { label: string; value: string; accent?: string }) {
  const colorMap: Record<string, string> = {
    signal: "text-signal",
    "status-success": "text-status-success",
    "status-warn": "text-status-warn",
  };
  return (
    <div className="panel p-4">
      <div className="text-xs text-ink-faint uppercase tracking-wide mb-2">{label}</div>
      <div className={`font-display text-2xl ${colorMap[accent]}`}>{value}</div>
    </div>
  );
}

function InsightRow({ icon, label, value }: { icon?: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center justify-between bg-base-800/50 rounded-lg px-3 py-2">
      <span className="flex items-center gap-1.5 text-ink-faint">
        {icon} {label}
      </span>
      <span className="text-ink-dim">{value}</span>
    </div>
  );
}
