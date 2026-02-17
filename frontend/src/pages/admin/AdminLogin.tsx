import { useState, useEffect } from "react";
import { useNavigate, NavLink } from "react-router-dom";
import { Admin } from "@/api/endpoints";
import { Shield, Key, User, Lock, CheckCircle2, AlertCircle, RefreshCw, Mail } from "lucide-react";

export default function AdminLogin() {
    const nav = useNavigate();
    const [loading, setLoading] = useState(false);
    const [checking, setChecking] = useState(true);
    const [hasAdmin, setHasAdmin] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [mode, setMode] = useState<"login" | "setup">("login");

    // Login State
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");

    // Setup State
    const [email, setEmail] = useState("");
    const [otp, setOtp] = useState("");
    const [otpSent, setOtpSent] = useState(false);

    useEffect(() => {
        checkAdminStatus();
    }, []);

    const checkAdminStatus = async () => {
        try {
            const res = await Admin.check();
            setHasAdmin(res.has_admin);
            if (!res.has_admin) setMode("setup");
        } catch (e) {
            console.error(e);
        } finally {
            setChecking(false);
        }
    };

    const generateOtp = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const res = await Admin.generateOtp(email);
            setSuccess(res.message || "Verification code sent to your email! (Check server console)");
            setOtpSent(true);
        } catch (e: any) {
            setError(e?.response?.data?.detail || "Failed to generate OTP");
        } finally {
            setLoading(false);
        }
    };

    const handleSetup = async (e: React.FormEvent) => {
        e.preventDefault();

        if (password !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }

        setLoading(true);
        setError(null);
        try {
            await Admin.setup({ username, password, email, otp });
            setSuccess("Admin account created successfully! Please login.");
            setHasAdmin(true); // Switch to login mode
            setOtpSent(false);
            setPassword(""); // Clear password for safety
        } catch (e: any) {
            setError(e?.response?.data?.detail || "Setup failed. Check OTP.");
        } finally {
            setLoading(false);
        }
    };

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const res = await Admin.login({ username, password });
            localStorage.setItem("admin_user", JSON.stringify(res));
            nav("/admin");
        } catch (e: any) {
            setError(e?.response?.data?.detail || "Invalid credentials");
        } finally {
            setLoading(false);
        }
    };

    if (checking) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center text-theme-text">
                <div className="animate-spin text-theme-accent">
                    <RefreshCw size={32} />
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-theme-bg flex items-center justify-center p-4">
            <div className="max-w-md w-full bg-theme-surface border border-theme-border rounded-xl shadow-2xl p-8 space-y-6 animate-in fade-in zoom-in duration-300">

                <div className="text-center space-y-2">
                    <div className="inline-flex p-3 rounded-full bg-theme-accent/20 text-theme-accent mb-2">
                        <Shield size={32} />
                    </div>
                    <h1 className="text-2xl font-bold text-theme-text">
                        {hasAdmin ? "Admin Portal" : "Admin Setup"}
                    </h1>
                    <p className="text-theme-text-secondary text-sm">
                        {mode === "login"
                            ? "Enter your credentials to access system controls."
                            : "Welcome! Verify your email to set up the admin account."}
                    </p>
                </div>

                {/* Error / Success Messages */}
                {error && (
                    <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-3 rounded-lg text-sm flex items-center gap-2">
                        <AlertCircle size={16} />
                        {error}
                    </div>
                )}
                {success && (
                    <div className="bg-green-500/10 border border-green-500/50 text-green-500 p-3 rounded-lg text-sm flex items-center gap-2">
                        <CheckCircle2 size={16} />
                        {success}
                    </div>
                )}

                {mode === "login" ? (
                    /* LOGIN FORM */
                    <form onSubmit={handleLogin} className="space-y-4">
                        <div className="space-y-1">
                            <label className="text-xs font-semibold uppercase text-theme-text-secondary">Username</label>
                            <div className="relative">
                                <User size={18} className="absolute left-3 top-2.5 text-theme-text-secondary" />
                                <input
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="w-full bg-theme-bg border border-theme-border rounded-lg py-2 pl-10 pr-4 text-theme-text focus:border-theme-accent focus:ring-1 focus:ring-theme-accent outline-none transition-all"
                                    placeholder="admin"
                                    required
                                />
                            </div>
                        </div>

                        <div className="space-y-1">
                            <label className="text-xs font-semibold uppercase text-theme-text-secondary">Password</label>
                            <div className="relative">
                                <Lock size={18} className="absolute left-3 top-2.5 text-theme-text-secondary" />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full bg-theme-bg border border-theme-border rounded-lg py-2 pl-10 pr-4 text-theme-text focus:border-theme-accent focus:ring-1 focus:ring-theme-accent outline-none transition-all"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-theme-accent hover:bg-theme-accent-hover text-theme-bg font-bold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                        >
                            {loading && <RefreshCw size={16} className="animate-spin" />}
                            {loading ? "Authenticating..." : "Login to Dashboard"}
                        </button>

                        <div className="text-center pt-2 space-y-2">
                            <p className="text-xs text-theme-text-secondary">
                                Need a new Admin account?{" "}
                                <button
                                    type="button"
                                    onClick={() => setMode("setup")}
                                    className="text-theme-accent hover:underline font-semibold"
                                >
                                    Sign up as Admin
                                </button>
                            </p>
                            <p className="text-xs text-theme-text-secondary border-t border-theme-border/30 pt-2">
                                New student? <NavLink to="/signup" className="text-theme-accent hover:underline font-semibold">Create Student Account</NavLink>
                            </p>
                        </div>
                    </form>
                ) : (
                    /* SETUP FORM */
                    <div className="space-y-6">
                        {!otpSent ? (
                            <form onSubmit={generateOtp} className="space-y-4">
                                <div className="bg-theme-bg/50 p-4 rounded-lg border border-theme-border border-dashed space-y-3">
                                    <p className="text-sm text-theme-text-secondary">
                                        Please enter your email address. We will send a verification code to this email to verify your identity.
                                    </p>

                                    <div className="space-y-1">
                                        <label className="text-xs font-semibold uppercase text-theme-text-secondary">Email Address</label>
                                        <div className="relative">
                                            <Mail size={18} className="absolute left-3 top-2.5 text-theme-text-secondary" />
                                            <input
                                                type="email"
                                                value={email}
                                                onChange={(e) => setEmail(e.target.value)}
                                                className="w-full bg-theme-bg border border-theme-border rounded-lg py-2 pl-10 pr-4 text-theme-text focus:border-theme-accent focus:ring-1 focus:ring-theme-accent outline-none transition-all"
                                                placeholder="admin@school.com"
                                                required
                                            />
                                        </div>
                                    </div>

                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className="w-full bg-theme-surface border border-theme-accent text-theme-accent hover:bg-theme-accent hover:text-theme-bg font-medium py-2 rounded-lg transition-colors"
                                    >
                                        {loading ? "Sending..." : "Generate Verification Code"}
                                    </button>
                                </div>
                            </form>
                        ) : (
                            <form onSubmit={handleSetup} className="space-y-4 animate-in slide-in-from-right-4 duration-300">
                                <div className="space-y-1">
                                    <div className="flex justify-between items-center mb-1">
                                        <label className="text-xs font-semibold uppercase text-theme-text-secondary">Verification Code</label>
                                        <button
                                            type="button"
                                            onClick={generateOtp}
                                            className="text-xs text-theme-accent hover:text-theme-accent-hover hover:underline transition-colors"
                                        >
                                            Generate New Code
                                        </button>
                                    </div>
                                    <div className="relative">
                                        <Key size={18} className="absolute left-3 top-2.5 text-theme-text-secondary" />
                                        <input
                                            value={otp}
                                            onChange={(e) => setOtp(e.target.value)}
                                            className="w-full bg-theme-bg border border-theme-border rounded-lg py-2 pl-10 pr-4 text-theme-text focus:border-theme-accent focus:ring-1 focus:ring-theme-accent outline-none transition-all tracking-widest font-mono"
                                            placeholder="XXXXXX"
                                            required
                                        />
                                    </div>
                                    <p className="text-xs text-theme-text-secondary">Sent to: {email}</p>
                                </div>

                                <div className="border-t border-theme-border/50 my-4"></div>

                                <div className="space-y-1">
                                    <label className="text-xs font-semibold uppercase text-theme-text-secondary">Set Username</label>
                                    <div className="relative">
                                        <User size={18} className="absolute left-3 top-2.5 text-theme-text-secondary" />
                                        <input
                                            value={username}
                                            onChange={(e) => setUsername(e.target.value)}
                                            className="w-full bg-theme-bg border border-theme-border rounded-lg py-2 pl-10 pr-4 text-theme-text focus:border-theme-accent focus:ring-1 focus:ring-theme-accent outline-none transition-all"
                                            placeholder="admin"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 gap-3">
                                    <div className="space-y-1">
                                        <label className="text-xs font-semibold uppercase text-theme-text-secondary">Set Password</label>
                                        <div className="relative">
                                            <Lock size={18} className="absolute left-3 top-2.5 text-theme-text-secondary" />
                                            <input
                                                type="password"
                                                value={password}
                                                onChange={(e) => setPassword(e.target.value)}
                                                className="w-full bg-theme-bg border border-theme-border rounded-lg py-2 pl-10 pr-4 text-theme-text focus:border-theme-accent focus:ring-1 focus:ring-theme-accent outline-none transition-all"
                                                placeholder="New Password"
                                                required
                                            />
                                        </div>
                                    </div>

                                    <div className="space-y-1">
                                        <label className="text-xs font-semibold uppercase text-theme-text-secondary">Confirm Password</label>
                                        <div className="relative">
                                            <Lock size={18} className="absolute left-3 top-2.5 text-theme-text-secondary" />
                                            <input
                                                type="password"
                                                value={confirmPassword}
                                                onChange={(e) => setConfirmPassword(e.target.value)}
                                                className={`w-full bg-theme-bg border rounded-lg py-2 pl-10 pr-4 text-theme-text focus:ring-1 outline-none transition-all ${confirmPassword && password !== confirmPassword
                                                    ? "border-red-500 focus:border-red-500 focus:ring-red-500"
                                                    : "border-theme-border focus:border-theme-accent focus:ring-theme-accent"
                                                    }`}
                                                placeholder="Confirm Password"
                                                required
                                            />
                                        </div>
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full bg-theme-accent hover:bg-theme-accent-hover text-theme-bg font-bold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                                >
                                    {loading && <RefreshCw size={16} className="animate-spin" />}
                                    {loading ? "Verifying..." : "Create Admin Account"}
                                </button>

                                {hasAdmin && (
                                    <div className="text-center pt-2">
                                        <button
                                            type="button"
                                            onClick={() => setMode("login")}
                                            className="text-xs text-theme-accent hover:underline"
                                        >
                                            ← Back to Admin Login
                                        </button>
                                    </div>
                                )}
                            </form>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
