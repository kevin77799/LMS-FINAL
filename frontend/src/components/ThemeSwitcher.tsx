import { useTheme } from "@/context/ThemeContext";
import { Palette } from "lucide-react";

export default function ThemeSwitcher() {
    const { theme, setTheme } = useTheme();

    return (
        <div className="flex items-center gap-2 mt-4 px-2">
            <div className="flex gap-2">
                <button
                    onClick={() => setTheme('emerald')}
                    className={`w-6 h-6 rounded-full border-2 transition-all ${theme === 'emerald' ? 'border-white scale-110' : 'border-transparent opacity-50 hover:opacity-100'
                        }`}
                    style={{ backgroundColor: '#10b981' }} // Emerald 500
                    title="Emerald Theme"
                />
                <button
                    onClick={() => setTheme('crimson')}
                    className={`w-6 h-6 rounded-full border-2 transition-all ${theme === 'crimson' ? 'border-white scale-110' : 'border-transparent opacity-50 hover:opacity-100'
                        }`}
                    style={{ backgroundColor: '#ef4444' }} // Red 500
                    title="Crimson Theme"
                />
                <button
                    onClick={() => setTheme('cyber')}
                    className={`w-6 h-6 rounded-full border-2 transition-all ${theme === 'cyber' ? 'border-white scale-110' : 'border-transparent opacity-50 hover:opacity-100'
                        }`}
                    style={{ backgroundColor: '#d946ef' }} // Fuchsia 500
                    title="Cyber Theme"
                />
            </div>
            <span className="text-xs text-gray-400 font-medium uppercase tracking-wider ml-1">
                {theme}
            </span>
        </div>
    );
}
