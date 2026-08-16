import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Zap, ArrowRight, Loader2 } from "lucide-react";
import { useAuth } from "../lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("dispatcher@routexai.com");
  const [password, setPassword] = useState("Dispatch@123");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || "/";

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Login failed. Check your credentials.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-base-950 bg-grid-fade px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 justify-center mb-8">
          <div className="w-9 h-9 rounded-lg bg-signal/15 border border-signal/40 flex items-center justify-center">
            <Zap size={18} className="text-signal" />
          </div>
          <span className="font-display text-xl font-semibold text-ink">RouteXAI</span>
        </div>

        <div className="panel p-6">
          <h1 className="font-display text-lg text-ink mb-1">Sign in</h1>
          <p className="text-sm text-ink-faint mb-6">Access the logistics command center.</p>

          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-ink-dim mb-1.5">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-base-800 border border-panelBorder rounded-lg px-3 py-2 text-sm text-ink outline-none focus:border-signal/60"
              />
            </div>
            <div>
              <label className="block text-xs text-ink-dim mb-1.5">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-base-800 border border-panelBorder rounded-lg px-3 py-2 text-sm text-ink outline-none focus:border-signal/60"
              />
            </div>

            {error && (
              <div className="text-xs text-status-danger bg-status-danger/10 border border-status-danger/25 rounded-lg px-3 py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full flex items-center justify-center gap-2 bg-signal text-base-950 font-medium text-sm rounded-lg py-2.5 hover:bg-signal-glow transition-colors disabled:opacity-60"
            >
              {submitting ? <Loader2 size={16} className="animate-spin" /> : <ArrowRight size={16} />}
              Sign in
            </button>
          </form>

          <div className="mt-5 text-xs text-ink-faint space-y-1 border-t border-panelBorder pt-4">
            <p className="text-ink-dim mb-1">Demo credentials:</p>
            <p>Admin: admin@routexai.com / Admin@123</p>
            <p>Dispatcher: dispatcher@routexai.com / Dispatch@123</p>
            <p>Rider: rider1@routexai.com / Rider@123</p>
          </div>
        </div>

        <p className="text-center text-xs text-ink-faint mt-4">
          No account?{" "}
          <Link to="/register" className="text-signal hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
