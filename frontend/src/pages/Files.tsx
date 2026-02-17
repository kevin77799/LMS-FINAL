import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Files as F, Groups } from "@/api/endpoints";
import type { FileItem } from "@/types/index";

export default function Files() {
  const nav = useNavigate();
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  const [groupId, setGroupId] = useState<number | null>(
    Number(localStorage.getItem("group_id")) || null
  );

  useEffect(() => {
    if (groupId) localStorage.setItem("group_id", String(groupId));
  }, [groupId]);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [file, setFile] = useState<File | undefined>();

  const load = async (gid: number) => {
    const r = await F.list(gid);
    setFiles(r);
  };

  useEffect(() => {
    if (!user?.username) nav("/login");
  }, [user, nav]);

  useEffect(() => {
    if (groupId) load(groupId);
  }, [groupId]);

  const createGroup = async () => {
    const name = prompt("New group name?");
    if (!name) return;
    const res = await Groups.create(user.user_id, name);
    const gid = res.group_id;
    localStorage.setItem("group_id", String(gid));
    setGroupId(gid);
  };

  const upload = async () => {
    if (!groupId || !file) return;
    await F.upload(groupId, file);
    await load(groupId);
  };

  const del = async (fid: number) => {
    await F.delete(fid);
    if (groupId) await load(groupId);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold mb-4 text-theme-accent">Files</h1>

      {/* Action Panel */}
      <div className="mb-8 p-6 bg-theme-surface border border-theme-border rounded-md space-y-4">
        <h3 className="font-semibold text-theme-text">File Upload & Grouping</h3>
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex flex-col gap-2">
            <label className="text-sm">Select File</label>
            <input
              type="file"
              onChange={(e) => setFile(e.target.files?.[0])}
              className="px-3 py-2 rounded-md bg-theme-bg border border-theme-border outline-none text-theme-text"
            />
          </div>
          <button
            onClick={upload}
            className="px-4 py-2 rounded-md bg-theme-accent text-theme-bg font-medium hover:bg-theme-accent-hover transition-colors"
          >
            Upload
          </button>
          <button
            onClick={createGroup}
            className="px-4 py-2 rounded-md bg-theme-surface border border-theme-border hover:bg-theme-bg text-theme-text text-sm transition-colors"
          >
            Create New Group
          </button>
        </div>
      </div>

      {/* Group ID */}
      <div className="flex gap-2 mb-4">
        <input
          placeholder="Current Group ID"
          value={groupId ?? ""}
          onChange={(e) => setGroupId(Number(e.target.value))}
          className="px-3 py-2 rounded-md bg-theme-surface border border-theme-border outline-none text-theme-text"
        />
      </div>

      {/* Files List */}
      <ul className="space-y-3">
        {files.map((f) => (
          <li
            key={f.id}
            className="p-3 border border-theme-border rounded-md flex justify-between items-center bg-theme-surface"
          >
            <div>
              <p className="font-medium text-theme-text">{f.file_name}</p>
              <p className="text-xs text-theme-text-secondary">{f.uploaded_at}</p>
            </div>
            <button
              onClick={() => del(f.id)}
              className="px-3 py-1 rounded-md bg-theme-accent hover:bg-theme-accent-hover text-theme-bg text-sm"
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
