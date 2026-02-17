import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Performance as Perf } from "@/api/endpoints";

export default function Performance() {
  const nav = useNavigate();
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  const [groupId, setGroupId] = useState<number | null>(
    Number(localStorage.getItem("group_id")) || null
  );
  const [items, setItems] = useState<any[]>([]);

  const load = async () => {
    if (!groupId) return;
    const r = await Perf.list(groupId, user.user_id);
    setItems(r);
  };

  useEffect(() => {
    load();
  }, [groupId]);

  if (!user?.username) {
    nav("/login");
    return null;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold mb-4 text-theme-accent">Performance</h1>

      {/* Group ID input */}
      <div className="flex gap-3 mb-6">
        <input
          type="number"
          placeholder="Group ID"
          value={groupId ?? ""}
          onChange={(e) => setGroupId(Number(e.target.value))}
          className="flex-1 px-4 py-2 rounded-md bg-theme-surface border border-theme-border focus:outline-none focus:ring-2 focus:ring-theme-accent text-theme-text"
        />
        <button
          onClick={load}
          className="px-4 py-2 bg-theme-accent text-theme-bg rounded-md hover:bg-theme-accent-hover transition"
        >
          Refresh
        </button>
      </div>

      {/* Performance items */}
      {items.length === 0 ? (
        <p className="text-theme-text-secondary">No performance records found.</p>
      ) : (
        <ul className="space-y-4">
          {items.map((it, idx) => (
            <li
              key={idx}
              className="p-4 bg-theme-surface border border-theme-border rounded-md flex justify-between items-center"
            >
              <div>
                <p className="font-medium text-theme-text">{it.subject}</p>
                <p className="text-xs text-theme-text-secondary">
                  {new Date(it.quiz_date).toLocaleString()}
                </p>
              </div>
              <span className="px-3 py-1 bg-theme-accent text-theme-bg rounded-md text-sm font-bold">
                {it.total_marks}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
