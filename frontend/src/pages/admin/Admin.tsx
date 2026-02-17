import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Admin } from "@/api/endpoints";

export default function AdminPage() {
  const nav = useNavigate();
  const [users, setUsers] = useState<any[]>([]);
  const [courses, setCourses] = useState<string[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<string>("");
  const [courseUsers, setCourseUsers] = useState<any[]>([]);
  const [newUser, setNewUser] = useState({
    username: "",
    password: "",
    course_id: "",
    education_level: "10",
  });
  const [selectedUser, setSelectedUser] = useState<number | null>(null);
  const [userGroups, setUserGroups] = useState<any[]>([]);
  const [groupName, setGroupName] = useState("");
  const [selectedGroup, setSelectedGroup] = useState<number | null>(null);
  const [groupFiles, setGroupFiles] = useState<any[]>([]);
  const [file, setFile] = useState<File | undefined>();
  const [courseSyllabus, setCourseSyllabus] = useState("");
  const [adminCode, setAdminCode] = useState("");
  const [adminId, setAdminId] = useState<number | null>(null);
  const [cameFromStudentDashboard, setCameFromStudentDashboard] = useState(false);

  const load = async () => {
    try {
      const [u, c] = await Promise.all([Admin.listUsers(), Admin.listCourses()]);
      setUsers(u);
      setCourses(c);
    } catch (e) {
      nav("/admin/login");
    }
  };

  useEffect(() => {
    const adminStr = localStorage.getItem("admin_user");
    if (!adminStr) {
      nav("/admin/login");
      return;
    }

    const userStr = localStorage.getItem("user");
    if (userStr) {
      setCameFromStudentDashboard(true);
    }

    const admin = JSON.parse(adminStr);
    setAdminId(admin.admin_id);
    setAdminCode(admin.admin_code);
    load();
  }, [nav]);

  const handleLogout = () => {
    localStorage.removeItem("admin_user");
    if (cameFromStudentDashboard) {
      nav("/app/dashboard");
    } else {
      nav("/");
    }
  };

  const createUser = async () => {
    if (!adminId) return;
    try {
      if (!newUser.username || !newUser.password || !newUser.course_id) {
        return alert("Fill all fields");
      }
      await Admin.createUser({ ...newUser, admin_id: adminId });
      alert("User created");
      setNewUser({ username: "", password: "", course_id: "", education_level: "10" });
      await load();
    } catch (err) {
      alert("Failed to create user");
    }
  };

  const loadCourseUsers = async () => {
    if (!selectedCourse) return;
    const u = await Admin.usersByCourse(selectedCourse);
    setCourseUsers(u);
  };

  const loadUserGroups = async (uid: number) => {
    setSelectedUser(uid);
    const g = await Admin.groupsForUser(uid);
    setUserGroups(g);
    setSelectedGroup(null);
    setGroupFiles([]);
  };

  const createGroup = async () => {
    if (!selectedUser || !groupName) return;
    await Admin.createGroup(selectedUser, groupName);
    setGroupName("");
    await loadUserGroups(selectedUser);
  };

  const loadGroupFiles = async (gid: number) => {
    setSelectedGroup(gid);
    const files = await Admin.listFiles(gid);
    setGroupFiles(files);
  };

  const upload = async () => {
    if (!selectedGroup || !file) return;
    try {
      await Admin.uploadToGroup(selectedGroup, file);
      alert("Uploaded");
      setFile(undefined);
      await loadGroupFiles(selectedGroup);
    } catch (err) {
      alert("Upload failed");
    }
  };

  const deleteFile = async (fid: number) => {
    if (!window.confirm("Delete this file?")) return;
    await Admin.deleteFile(fid);
    if (selectedGroup) await loadGroupFiles(selectedGroup);
  };

  const loadCourseSyllabus = async () => {
    if (!selectedCourse) return;
    const r = await Admin.getCourseSyllabus(selectedCourse);
    setCourseSyllabus(r.syllabus_content || "");
  };

  const saveCourseSyllabus = async () => {
    if (!selectedCourse) return;
    await Admin.saveCourseSyllabus(selectedCourse, courseSyllabus);
    alert("Saved syllabus");
  };

  return (
    <div className="min-h-screen bg-[#0f1117] text-white p-8 space-y-8">
      {/* Header */}
      <div className="bg-indigo-600/20 border border-indigo-600 p-6 rounded-lg shadow flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-indigo-400">Admin Dashboard</h1>
          <p className="text-gray-400 text-sm">System Control Center</p>
        </div>
        <div className="text-right flex flex-col items-end gap-2">
          <button onClick={handleLogout} className="text-xs text-red-400 hover:text-red-300 border border-red-500/30 px-2 py-1 rounded">
            {cameFromStudentDashboard ? "Exit to Student Portal" : "Logout"}
          </button>
          <div className="text-right">
            <p className="text-xs text-gray-400 uppercase font-bold tracking-wider">Admin Code</p>
            <p className="text-3xl font-mono font-bold text-white tracking-widest">{adminCode || "..."}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Section 1: User Management */}
        <div className="space-y-8">
          <div className="bg-[#1e1f26] p-6 rounded-lg shadow space-y-4 border border-gray-800">
            <h2 className="text-xl font-semibold mb-4 text-indigo-400">Create New User</h2>
            <div className="grid grid-cols-2 gap-3">
              <input type="text" placeholder="Username" value={newUser.username} onChange={(e) => setNewUser({ ...newUser, username: e.target.value })} className="px-4 h-10 rounded bg-[#2a2d35] border border-gray-700 outline-none focus:border-indigo-500" />
              <input type="password" placeholder="Password" value={newUser.password} onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} className="px-4 h-10 rounded bg-[#2a2d35] border border-gray-700 outline-none focus:border-indigo-500" />
              <input type="text" placeholder="Course ID (e.g. IT-101)" value={newUser.course_id} onChange={(e) => setNewUser({ ...newUser, course_id: e.target.value })} className="px-4 h-10 rounded bg-[#2a2d35] border border-gray-700 outline-none focus:border-indigo-500" />
              <select value={newUser.education_level} onChange={(e) => setNewUser({ ...newUser, education_level: e.target.value })} className="px-4 h-10 rounded bg-[#2a2d35] border border-gray-700 outline-none focus:border-indigo-500">
                {["8", "9", "10", "11", "12"].map((g) => <option key={g} value={g}>Grade {g}</option>)}
              </select>
            </div>
            <button onClick={createUser} className="w-full py-2 bg-indigo-600 rounded hover:bg-indigo-700 transition font-bold">Register Student</button>
          </div>

          <div className="bg-[#1e1f26] p-6 rounded-lg shadow space-y-4 border border-gray-800">
            <h2 className="text-xl font-semibold mb-4 text-indigo-400">Users & Groups</h2>
            <div className="flex gap-2">
              <select value={selectedCourse} onChange={(e) => setSelectedCourse(e.target.value)} className="flex-1 h-10 px-4 rounded bg-[#2a2d35] border border-gray-700 outline-none">
                <option value="">Filter by Course</option>
                {courses.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
              <button onClick={loadCourseUsers} className="px-4 py-2 bg-indigo-600 rounded hover:bg-indigo-700 transition">Load</button>
            </div>
            <div className="max-h-60 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
              {courseUsers.map((u) => (
                <div key={u.id} className={`p-3 rounded border transition cursor-pointer ${selectedUser === u.id ? 'bg-indigo-600/20 border-indigo-500' : 'bg-[#2a2d35] border-gray-700'}`} onClick={() => loadUserGroups(u.id)}>
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{u.username}</span>
                    <span className="text-xs text-gray-500">ID: {u.id}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Section 2: Group & File Management */}
        <div className="space-y-8">
          {selectedUser && (
            <div className="bg-[#1e1f26] p-6 rounded-lg shadow space-y-4 border border-gray-800 animate-in fade-in duration-300">
              <h2 className="text-xl font-semibold text-indigo-400">Study Groups (User #{selectedUser})</h2>
              <div className="flex gap-2">
                <input type="text" placeholder="Group Name" value={groupName} onChange={(e) => setGroupName(e.target.value)} className="flex-1 h-10 px-4 rounded bg-[#2a2d35] border border-gray-700 outline-none focus:border-indigo-500" />
                <button onClick={createGroup} className="px-4 bg-green-600 rounded hover:bg-green-700 transition">Create</button>
              </div>
              <div className="grid grid-cols-1 gap-2">
                {userGroups.map((g) => (
                  <div key={g.id} className={`p-3 rounded border flex justify-between items-center cursor-pointer transition ${selectedGroup === g.id ? 'bg-green-600/20 border-green-500' : 'bg-[#2a2d35] border-gray-700'}`} onClick={() => loadGroupFiles(g.id)}>
                    <span>{g.group_name}</span>
                    <span className="text-xs text-gray-400">ID: {g.id}</span>
                  </div>
                ))}
              </div>

              {selectedGroup && (
                <div className="mt-6 pt-6 border-t border-gray-800 space-y-4 animate-in slide-in-from-top-2">
                  <h3 className="text-lg font-medium text-green-400">Group Files (Group #{selectedGroup})</h3>
                  <div className="space-y-2 bg-[#0f1117] p-3 rounded-md">
                    {groupFiles.length === 0 && <p className="text-xs text-gray-500 italic">No files in this group.</p>}
                    {groupFiles.map(f => (
                      <div key={f.id} className="flex justify-between items-center text-sm p-2 hover:bg-white/5 rounded">
                        <span className="truncate flex-1 pr-4">{f.file_name}</span>
                        <button onClick={(e) => { e.stopPropagation(); deleteFile(f.id); }} className="text-red-400 hover:text-red-300 text-xs px-2 py-1">Delete</button>
                      </div>
                    ))}
                  </div>
                  <div className="flex flex-col gap-3">
                    <input type="file" onChange={(e) => setFile(e.target.files?.[0])} className="text-xs text-gray-400 block w-full file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-700 cursor-pointer" />
                    <button onClick={upload} disabled={!file} className="w-full py-2 bg-green-600 rounded hover:bg-green-700 transition disabled:opacity-50 font-bold">Upload to Group</button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Syllabus Editor */}
          <div className="bg-[#1e1f26] p-6 rounded-lg shadow space-y-4 border border-gray-800">
            <h2 className="text-xl font-semibold text-indigo-400">Course Syllabus Editor</h2>
            <div className="flex gap-2">
              <select value={selectedCourse} onChange={(e) => setSelectedCourse(e.target.value)} className="flex-1 h-10 px-4 rounded bg-[#2a2d35] border border-gray-700 outline-none">
                <option value="">Select Course</option>
                {courses.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
              <button onClick={loadCourseSyllabus} disabled={!selectedCourse} className="px-4 py-2 bg-indigo-600 rounded hover:bg-indigo-700 transition disabled:opacity-50">Load</button>
            </div>
            <textarea value={courseSyllabus} onChange={(e) => setCourseSyllabus(e.target.value)} placeholder="Enter one topic per line..." className="w-full h-48 px-4 py-3 rounded bg-[#2a2d35] border border-gray-700 outline-none focus:border-indigo-500 resize-none font-mono text-sm" />
            <button onClick={saveCourseSyllabus} disabled={!selectedCourse} className="w-full py-2 bg-green-600 rounded hover:bg-green-700 transition disabled:opacity-50 font-bold">Save Course Syllabus</button>
          </div>
        </div>
      </div>
    </div>
  );
}
