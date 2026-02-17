import { useState } from "react";
import { useNavigate, NavLink } from "react-router-dom";
import { Admin } from "@/api/endpoints";
import { User, Lock, BookOpen, GraduationCap, Shield, RefreshCw, CheckCircle2, AlertCircle } from "lucide-react";

export default function Signup() {
    const nav = useNavigate();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const [formData, setFormData] = useState({
        username: "",
        password: "",
        course_id: "",
        education_level: "",
        admin_code: "" // This is the secret code from the admin
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSignup = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            await Admin.signup(formData);
            setSuccess("Account created successfully! Redirecting to login...");
            setTimeout(() => nav("/login"), 2000);
        } catch (err: any) {
            setError(err?.response?.data?.detail || "Signup failed. Is your Admin Code correct?");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-theme-bg flex items-center justify-center p-4">
            <div className="max-w-md w-full bg-theme-surface border border-theme-border rounded-xl shadow-2xl p-8 space-y-6 animate-in fade-in zoom-in duration-300">

                <div className="text-center space-y-2">
                    <h1 className="text-3xl font-bold text-theme-text font-outfit">Join StudentAI</h1>
                    <p className="text-theme-text-secondary text-sm">Create your student account to start learning.</p>
                </div>

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

                <form onSubmit={handleSignup} className="space-y-4">
                    {/* Admin Code */}
                    <div className="space-y-1">
                        <label className="text-xs font-semibold uppercase text-theme-text-secondary">Admin Verification Code</label>
                        <div className="relative">
                            <Shield size={18} className="absolute left-3 top-2.5 text-theme-accent" />
                            <input
                                name="admin_code"
                                value={formData.admin_code}
                                onChange={handleChange}
                                className="w-full bg-theme-bg border border-theme-border rounded-lg py-2.5 pl-10 pr-4 text-theme-text focus:border-theme-accent focus:ring-1 focus:ring-theme-accent outline-none transition-all font-mono tracking-widest uppercase"
                                placeholder="ABC123"
                                required
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        {/* Username */}
                        <div className="space-y-1">
                            <label className="text-xs font-semibold uppercase text-theme-text-secondary">Username</label>
                            <div className="relative">
                                <User size={18} className="absolute left-3 top-2.5 text-theme-text-secondary" />
                                <input
                                    name="username"
                                    value={formData.username}
                                    onChange={handleChange}
                                    className="w-full bg-theme-bg border border-theme-border rounded-lg py-2 pl-10 pr-4 text-theme-text focus:border-theme-accent focus:ring-1 focus:ring-theme-accent outline-none"
                                    placeholder="alex24"
                                    required
                                />
                            </div>
                        </div>

                        {/* Password */}
                        <div className="space-y-1">
                            <label className="text-xs font-semibold uppercase text-theme-text-secondary">Password</label>
                            <div className="relative">
                                <Lock size={18} className="absolute left-3 top-2.5 text-theme-text-secondary" />
                                <input
                                    type="password"
                                    name="password"
                                    value={formData.password}
                                    onChange={handleChange}
                                    className="w-full bg-theme-bg border border-theme-border rounded-lg py-2 pl-10 pr-4 text-theme-text focus:border-theme-accent focus:ring-1 focus:ring-theme-accent outline-none"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        </div>
                    </div>

                    {/* Education Level */}
                    <div className="space-y-1">
                        <label className="text-xs font-semibold uppercase text-theme-text-secondary">Education Level</label>
                        <div className="relative">
                            <GraduationCap size={18} className="absolute left-3 top-2.5 text-theme-text-secondary" />
                            <select
                                name="education_level"
                                value={formData.education_level}
                                onChange={handleChange as any}
                                className="w-full bg-theme-bg border border-theme-border rounded-lg py-2 pl-10 pr-4 text-theme-text focus:border-theme-accent focus:ring-1 focus:ring-theme-accent outline-none appearance-none"
                                required
                            >
                                <option value="">Select Level</option>
                                <option value="High School">High School</option>
                                <option value="Bachelors">Bachelors</option>
                                <option value="Masters">Masters</option>
                                <option value="PhD">PhD</option>
                            </select>
                        </div>
                    </div>

                    {/* Course/Subject */}
                    <div className="space-y-1">
                        <label className="text-xs font-semibold uppercase text-theme-text-secondary">Course / Subject</label>
                        <div className="relative">
                            <BookOpen size={18} className="absolute left-3 top-2.5 text-theme-text-secondary" />
                            <input
                                name="course_id"
                                value={formData.course_id}
                                onChange={handleChange}
                                className="w-full bg-theme-bg border border-theme-border rounded-lg py-2 pl-10 pr-4 text-theme-text focus:border-theme-accent focus:ring-1 focus:ring-theme-accent outline-none"
                                placeholder="Computer Science"
                                required
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-theme-accent hover:bg-theme-accent-hover text-theme-bg font-bold py-3 rounded-lg transition-all transform hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-2 mt-4 shadow-lg shadow-theme-accent/20"
                    >
                        {loading && <RefreshCw size={18} className="animate-spin" />}
                        {loading ? "Creating Account..." : "Create Student Account"}
                    </button>
                </form>

                <div className="text-center pt-4 border-t border-theme-border/50">
                    <p className="text-sm text-theme-text-secondary">
                        Already have an account?{" "}
                        <NavLink to="/login" className="text-theme-accent font-semibold hover:underline">
                            Log in
                        </NavLink>
                    </p>
                </div>
            </div>
        </div>
    );
}
