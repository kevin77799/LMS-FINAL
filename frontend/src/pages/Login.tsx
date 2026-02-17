import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Auth } from "@/api/endpoints";
import type { LoginResponse } from "../types";
import { ChevronLeft, ChevronRight, Eye, EyeOff, Shield } from "lucide-react";

export default function Login() {
  const nav = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Login Steps: 1 = Admin Code, 2 = Credentials
  const [step, setStep] = useState(1);
  const [adminCode, setAdminCode] = useState("");

  const [showPassword, setShowPassword] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = (await Auth.login(username, password, adminCode)) as LoginResponse;
      localStorage.removeItem("admin_user"); // Clear any leftover admin session
      localStorage.setItem("user", JSON.stringify(data));
      nav("/app/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-theme-bg text-theme-text">
      {/* SIDEBAR */}
      <div
        className={`bg-theme-surface transition-all duration-300 relative ${sidebarOpen ? "w-64" : "w-0"
          }`}
      >
        {sidebarOpen && (
          <div className="p-6">
            <div className="bg-theme-accent/20 text-theme-text px-4 py-2 rounded-lg shadow-md">
              <p className="font-medium">Please log in to continue.</p>
            </div>
          </div>
        )}
        {/* Toggle button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="absolute top-4 -right-4 bg-theme-surface border border-theme-border text-theme-text p-1 rounded-full shadow-md"
        >
          {sidebarOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
        </button>
      </div>

      {/* RIGHT CONTENT */}
      <div className="flex-1 flex items-center justify-center p-8 transition-all duration-300">
        <div className="w-[90%] mx-auto max-w-md">
          <h1 className="text-3xl font-bold mb-6">Student Analyzer AI</h1>
          <h2 className="text-xl font-semibold mb-4">Login</h2>

          <form onSubmit={step === 1 ? (e) => { e.preventDefault(); setStep(2); } : submit} className="space-y-4">

            {step === 1 && (
              <div className="space-y-4 animate-in slide-in-from-right duration-300">
                <div>
                  <label className="block text-sm font-medium mb-2">Admin Code</label>
                  <p className="text-xs text-theme-text-secondary mb-2">Enter the code provided by your administrator.</p>
                  <input
                    value={adminCode}
                    onChange={(e) => setAdminCode(e.target.value.toUpperCase())}
                    required
                    placeholder="e.g. ABC123"
                    className="w-full px-4 py-2 rounded-lg bg-theme-surface border border-theme-border 
                                       focus:border-theme-accent focus:ring-2 focus:ring-theme-accent outline-none tracking-widest font-mono text-center uppercase"
                  />
                </div>
                <button
                  type="submit"
                  disabled={!adminCode}
                  className="w-full border border-theme-border text-theme-text px-3 py-2 rounded-md text-sm font-medium
                                    hover:bg-theme-text hover:text-theme-bg transition duration-200"
                >
                  Next
                </button>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-4 animate-in slide-in-from-right duration-300">
                <div className="flex items-center justify-between p-2 bg-theme-surface/50 rounded-lg border border-theme-border/50">
                  <span className="text-xs font-mono text-theme-text-secondary">Code: {adminCode}</span>
                  <button type="button" onClick={() => setStep(1)} className="text-xs text-theme-accent hover:underline">Change</button>
                </div>

                {/* Username */}
                <div>
                  <label className="block text-sm font-medium mb-2">Username</label>
                  <input
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    className="w-full px-4 py-2 rounded-lg bg-theme-surface border border-theme-border 
                                   focus:border-theme-accent focus:ring-2 focus:ring-theme-accent outline-none"
                  />
                </div>

                {/* Password */}
                <div>
                  <label className="block text-sm font-medium mb-2">Password</label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      className="w-full px-4 py-2 rounded-lg bg-theme-surface border border-theme-border 
                                     focus:border-theme-accent focus:ring-2 focus:ring-theme-accent outline-none pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-3 flex items-center text-theme-text-secondary hover:text-theme-text"
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                {/* Button */}
                <button
                  disabled={loading}
                  className="w-full border border-theme-border text-theme-text px-3 py-2 rounded-md text-sm font-medium
                                hover:bg-theme-text hover:text-theme-bg transition duration-200"
                >
                  {loading ? "Signing in..." : "Login"}
                </button>
              </div>
            )}
          </form>

          {/* Error */}
          {/* Error */}
          {error && <p className="mt-4 text-theme-accent text-center">{error}</p>}

          {/* Admin Login Link */}
          <div className="mt-8 pt-4 border-t border-theme-border/30 flex justify-center">
            <button
              onClick={() => nav("/admin")}
              className="flex items-center gap-2 text-sm text-theme-text-secondary hover:text-theme-accent transition-colors opacity-70 hover:opacity-100"
            >
              <Shield size={16} />
              <span>Access Admin Portal</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
