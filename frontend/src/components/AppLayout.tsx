import { useState, useEffect } from "react";
import { useNavigate, NavLink, Outlet, useLocation } from "react-router-dom";
import {
    ChevronLeft,
    ChevronRight,
    LayoutDashboard,
    BookOpen,
    Lightbulb,
    FileQuestion,
    MessageSquare,
    FileText,
    TrendingUp,
    Settings,
    LogOut,
    UserCircle,
    Shield
} from "lucide-react";
import ThemeSwitcher from "@/components/ThemeSwitcher";

export default function AppLayout() {
    const nav = useNavigate();
    const location = useLocation();
    const user = JSON.parse(localStorage.getItem("user") || "{}");
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);

    useEffect(() => {
        if (!user?.username) {
            nav("/");
        }
    }, [user, nav]);

    const navItems = [
        { name: "Dashboard", path: "dashboard", icon: LayoutDashboard },
        { name: "Syllabus", path: "syllabus", icon: BookOpen },
        { name: "Recommendations", path: "recommendations", icon: Lightbulb },
        { name: "Quiz", path: "quiz", icon: FileQuestion },
        { name: "Chat", path: "chat", icon: MessageSquare },
        { name: "Files", path: "files", icon: FileText },
        { name: "Performance", path: "performance", icon: TrendingUp },
    ];

    return (
        <div className="flex min-h-screen bg-theme-bg text-theme-text transition-colors duration-300 font-sans">
            {/* SIDEBAR */}
            <div
                className={`bg-theme-surface/95 backdrop-blur-md border-r border-theme-border transition-all duration-300 relative flex flex-col ${sidebarOpen ? "w-64" : "w-20"
                    }`}
            >
                {/* Sidebar Header */}
                <div className="p-6 flex items-center justify-between">
                    {sidebarOpen ? (
                        <h1 className="text-xl font-bold text-theme-accent tracking-tight">StudentAI</h1>
                    ) : (
                        <h1 className="text-xl font-bold text-theme-accent tracking-tight text-center w-full">AI</h1>
                    )}
                </div>

                {/* User Info */}
                <div className={`px-6 pb-6 ${!sidebarOpen && "flex justify-center"}`}>
                    {sidebarOpen ? (
                        <div className="bg-theme-bg/50 p-3 rounded-lg border border-theme-border/50">
                            <p className="text-xs text-theme-text-secondary uppercase font-semibold">Welcome</p>
                            <p className="font-medium truncate">{user?.username}</p>
                        </div>
                    ) : (
                        <div title={user?.username} className="w-10 h-10 rounded-full bg-theme-accent/20 flex items-center justify-center text-theme-accent font-bold">
                            {user?.username?.charAt(0).toUpperCase()}
                        </div>
                    )}
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-4 space-y-1 overflow-y-auto">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.path}
                            to={`/app/${item.path}`}
                            className={({ isActive }) =>
                                `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${isActive
                                    ? "bg-theme-accent text-theme-bg font-semibold shadow-md shadow-theme-accent/20"
                                    : "text-theme-text-secondary hover:bg-theme-bg/50 hover:text-theme-text"
                                }`
                            }
                            title={!sidebarOpen ? item.name : ""}
                        >
                            <item.icon size={20} className={sidebarOpen ? "" : "mx-auto"} />
                            {sidebarOpen && <span>{item.name}</span>}
                        </NavLink>
                    ))}


                    {/* Settings Section */}
                    <div className="pt-2 mt-2 border-t border-theme-border/30">
                        <button
                            onClick={() => {
                                if (!sidebarOpen) setSidebarOpen(true);
                                setIsSettingsOpen(!isSettingsOpen);
                            }}
                            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${isSettingsOpen
                                ? "bg-theme-bg/50 text-theme-text"
                                : "text-theme-text-secondary hover:bg-theme-bg/50 hover:text-theme-text"
                                }`}
                            title={!sidebarOpen ? "Settings" : ""}
                        >
                            <Settings size={20} className={sidebarOpen ? "" : "mx-auto"} />
                            {sidebarOpen && <span className="flex-1 text-left">Settings</span>}
                        </button>

                        {sidebarOpen && isSettingsOpen && (
                            <div className="mt-2 ml-4 pl-4 border-l-2 border-theme-border/30 space-y-3 animate-in slide-in-from-top-2 duration-200">
                                {/* Theme Section */}
                                <div className="space-y-2">
                                    <p className="text-xs font-semibold text-theme-text-secondary uppercase">Appearance</p>
                                    <ThemeSwitcher />
                                </div>

                                {/* Admin Link */}
                                <div className="space-y-2 pt-2">
                                    <p className="text-xs font-semibold text-theme-text-secondary uppercase">System</p>
                                    <button
                                        onClick={() => nav("/admin/login")}
                                        className="flex items-center gap-2 text-sm text-theme-text hover:text-theme-accent transition-colors w-full"
                                    >
                                        <Shield size={16} />
                                        <span>Admin Login</span>
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </nav>

                {/* Sidebar Footer */}
                <div className="p-4 border-t border-theme-border/30">
                    <button
                        onClick={() => {
                            localStorage.clear();
                            nav("/");
                        }}
                        className={`flex items-center gap-3 w-full px-3 py-2 rounded-lg text-theme-text-secondary hover:bg-red-500/10 hover:text-red-500 transition-colors ${!sidebarOpen && "justify-center"}`}
                    >
                        {sidebarOpen ? (
                            <>
                                <LogOut size={20} />
                                <span className="font-medium">Logout</span>
                            </>
                        ) : (
                            <span className="font-bold text-xs text-red-500">Log</span>
                        )}
                    </button>
                </div>

                {/* Sidebar Toggle Button */}
                <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="absolute top-1/2 -right-3 transform -translate-y-1/2 bg-theme-surface border border-theme-border text-theme-text p-1.5 rounded-full shadow-lg hover:scale-110 transition-transform z-50"
                >
                    {sidebarOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
                </button>
            </div>

            {/* MAIN CONTENT AREA */}
            <div className="flex-1 flex flex-col h-screen overflow-hidden">
                {/* Header (Breadcrumb / Title) */}
                <header className="px-8 py-6 flex items-center justify-between bg-theme-bg/95 backdrop-blur-sm z-10 sticky top-0">
                    <div>
                        <h2 className="text-2xl font-bold text-theme-text capitalize tracking-tight">
                            {location.pathname.split("/").pop()?.replace("-", " ") || "Dashboard"}
                        </h2>
                        <p className="text-theme-text-secondary text-sm mt-1">
                            Manage your learning journey
                        </p>
                    </div>

                    {/* Decorative Element or Additional Controls could go here */}
                    <div className="h-2 w-20 bg-gradient-to-r from-theme-accent to-transparent rounded-full opacity-50"></div>
                </header>

                {/* Scrollable Page Content */}
                <main className="flex-1 overflow-y-auto px-8 pb-8">
                    <div className="max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div >
    );
}
