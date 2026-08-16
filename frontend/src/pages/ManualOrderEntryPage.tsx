import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, PlusCircle, Eraser, Loader2 } from "lucide-react";
import { ordersApi, extractError } from "../lib/api";
import type { OrderPriority } from "../lib/types";
import { useToast } from "../lib/toast";

const EMPTY = {
  customer_name: "",
  phone_number: "",
  address: "",
  latitude: "12.9716",
  longitude: "77.5946",
  priority: "Normal" as OrderPriority,
  time_window_start: "09:00",
  time_window_end: "18:00",
  package_weight: "2.0",
  special_instructions: "",
};

export default function ManualOrderEntryPage() {
  const [form, setForm] = useState(EMPTY);
  const [submitting, setSubmitting] = useState<"add" | "optimize" | null>(null);
  const { push } = useToast();
  const navigate = useNavigate();

  function update<K extends keyof typeof EMPTY>(key: K, value: (typeof EMPTY)[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function buildPayload() {
    return {
      customer_name: form.customer_name,
      phone_number: form.phone_number || undefined,
      address: form.address,
      latitude: parseFloat(form.latitude),
      longitude: parseFloat(form.longitude),
      priority: form.priority,
      time_window_start: form.time_window_start || undefined,
      time_window_end: form.time_window_end || undefined,
      package_weight: parseFloat(form.package_weight) || 1,
      special_instructions: form.special_instructions || undefined,
    };
  }

  async function handleSubmit(optimize: boolean) {
    if (!form.customer_name || !form.address) {
      push("error", "Customer name and address are required.");
      return;
    }
    setSubmitting(optimize ? "optimize" : "add");
    try {
      const order = await ordersApi.createManual(buildPayload(), optimize);
      push(
        "success",
        optimize
          ? `Order for ${order.customer_name} created and sent to the optimizer.`
          : `Order for ${order.customer_name} added.`
      );
      setForm(EMPTY);
      if (optimize) navigate("/fleet");
    } catch (err) {
      push("error", extractError(err).message);
    } finally {
      setSubmitting(null);
    }
  }

  return (
    <div className="max-w-2xl space-y-5">
      <div>
        <h1 className="font-display text-xl text-ink">Manual Order Entry</h1>
        <p className="text-sm text-ink-faint mt-1">
          Add a single delivery order directly, or send it straight to the optimizer.
        </p>
      </div>

      <div className="panel p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Customer Name" required>
            <input
              className="input"
              value={form.customer_name}
              onChange={(e) => update("customer_name", e.target.value)}
            />
          </Field>
          <Field label="Phone Number">
            <input
              className="input"
              value={form.phone_number}
              onChange={(e) => update("phone_number", e.target.value)}
            />
          </Field>
        </div>

        <Field label="Address" required>
          <input className="input" value={form.address} onChange={(e) => update("address", e.target.value)} />
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Latitude">
            <input
              className="input font-mono"
              value={form.latitude}
              onChange={(e) => update("latitude", e.target.value)}
            />
          </Field>
          <Field label="Longitude">
            <input
              className="input font-mono"
              value={form.longitude}
              onChange={(e) => update("longitude", e.target.value)}
            />
          </Field>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <Field label="Priority">
            <select
              className="input"
              value={form.priority}
              onChange={(e) => update("priority", e.target.value as OrderPriority)}
            >
              <option>Normal</option>
              <option>Express</option>
              <option>Emergency</option>
            </select>
          </Field>
          <Field label="Window Start">
            <input
              type="time"
              className="input"
              value={form.time_window_start}
              onChange={(e) => update("time_window_start", e.target.value)}
            />
          </Field>
          <Field label="Window End">
            <input
              type="time"
              className="input"
              value={form.time_window_end}
              onChange={(e) => update("time_window_end", e.target.value)}
            />
          </Field>
        </div>

        <Field label="Package Weight (kg)">
          <input
            type="number"
            step="0.1"
            className="input w-32"
            value={form.package_weight}
            onChange={(e) => update("package_weight", e.target.value)}
          />
        </Field>

        <Field label="Special Instructions">
          <textarea
            className="input"
            rows={2}
            value={form.special_instructions}
            onChange={(e) => update("special_instructions", e.target.value)}
          />
        </Field>

        <div className="flex items-center gap-2 pt-2 border-t border-panelBorder">
          <button
            onClick={() => handleSubmit(false)}
            disabled={submitting !== null}
            className="flex items-center gap-1.5 text-sm px-4 py-2.5 rounded-lg border border-panelBorder text-ink-dim hover:text-ink hover:border-signal/40 transition-colors disabled:opacity-60"
          >
            {submitting === "add" ? <Loader2 size={15} className="animate-spin" /> : <PlusCircle size={15} />}
            Add Order
          </button>
          <button
            onClick={() => handleSubmit(true)}
            disabled={submitting !== null}
            className="flex items-center gap-1.5 text-sm px-4 py-2.5 rounded-lg bg-signal text-base-950 font-medium hover:bg-signal-glow transition-colors disabled:opacity-60"
          >
            {submitting === "optimize" ? (
              <Loader2 size={15} className="animate-spin" />
            ) : (
              <Sparkles size={15} />
            )}
            Save &amp; Optimize
          </button>
          <button
            onClick={() => setForm(EMPTY)}
            className="ml-auto flex items-center gap-1.5 text-sm px-3 py-2.5 rounded-lg text-ink-faint hover:text-ink transition-colors"
          >
            <Eraser size={15} /> Clear Form
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-xs text-ink-dim mb-1.5">
        {label} {required && <span className="text-status-emergency">*</span>}
      </span>
      {children}
    </label>
  );
}
