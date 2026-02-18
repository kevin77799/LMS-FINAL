import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Admin, Updates } from "@/api/endpoints";
import {
  Users,
  BookOpen,
  BellRing,
  LogOut,
  Settings,
  LayoutDashboard,
  PlusCircle,
  FolderOpen,
  MessageSquare,
  FileText,
  Palette,
  CheckCircle2,
  Trash2,
  Upload,
  ExternalLink,
  ChevronRight
} from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

type SubTab = "users" | "groups" | "syllabus" | "materials" | "updates" | "polls";

export default function AdminPage() {
  const nav = useNavigate();
  const { theme, setTheme } = useTheme();

  // Navigation State
  const [activeTab, setActiveTab] = useState<SubTab>("users");
  const [cameFromStudentDashboard, setCameFromStudentDashboard] = useState(false);
  const [adminCode, setAdminCode] = useState("");
  const [adminId, setAdminId] = useState<number | null>(null);

  // Data State
  const [users, setUsers] = useState<any[]>([]);
  const [courses, setCourses] = useState<string[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<string>("");
  const [courseUsers, setCourseUsers] = useState<any[]>([]);
  const [newUser, setNewUser] = useState({
    username: "",
    password: "",
    course_id: "",
    education_level: "1",
  });
  const [selectedUser, setSelectedUser] = useState<number | null>(null);
  const [userGroups, setUserGroups] = useState<any[]>([]);
  const [groupName, setGroupName] = useState("");
  const [selectedGroup, setSelectedGroup] = useState<number | null>(null);
  const [groupFiles, setGroupFiles] = useState<any[]>([]);
  const [file, setFile] = useState<File | undefined>();
  const [courseSyllabus, setCourseSyllabus] = useState("");
  const [courseFiles, setCourseFiles] = useState<any[]>([]);
  const [courseFile, setCourseFile] = useState<File | undefined>();

  // Updates & Polls State
  const [updateContent, setUpdateContent] = useState("");
  const [updateUrl, setUpdateUrl] = useState("");
  const [updateImageFile, setUpdateImageFile] = useState<File | undefined>();
  const [pollQuestion, setPollQuestion] = useState("");
  const [pollOptions, setPollOptions] = useState<string[]>(["", ""]);

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

  // Handlers
  const createUser = async () => {
    if (!adminId) return;
    try {
      if (!newUser.username || !newUser.password || !newUser.course_id) {
        return alert("Fill all fields");
      }
      await Admin.createUser({ ...newUser, admin_id: adminId });
      alert("User created");
      setNewUser({ username: "", password: "", course_id: "", education_level: "1" });
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
    setActiveTab("groups");
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

  const uploadFile = async () => {
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

  const deleteFile = async (fid: number, isCourseFile = false) => {
    if (!window.confirm("Delete this file?")) return;
    await Admin.deleteFile(fid);
    if (isCourseFile && selectedCourse) {
      await loadCourseFiles();
    } else if (selectedGroup) {
      await loadGroupFiles(selectedGroup);
    }
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

  const loadCourseFiles = async () => {
    if (!selectedCourse) return;
    const files = await Admin.listCourseFiles(selectedCourse);
    setCourseFiles(files);
  };

  const uploadCourseFile = async () => {
    if (!selectedCourse || !courseFile) return;
    try {
      await Admin.uploadCourseFile(selectedCourse, courseFile);
      alert("Uploaded to Course");
      setCourseFile(undefined);
      await loadCourseFiles();
    } catch (err) {
      alert("Upload failed");
    }
  };

  const handleUpdateSubmit = async () => {
    if (!selectedCourse || !updateContent) return alert("Select course and enter content");
    try {
      await Updates.createUpdate(selectedCourse, updateContent, updateImageFile, updateUrl);
      alert("Update posted!");
      setUpdateContent("");
      setUpdateUrl("");
      setUpdateImageFile(undefined);
    } catch (err) {
      alert("Failed to post update");
    }
  };

  const handlePollSubmit = async () => {
    if (!selectedCourse || !pollQuestion) return alert("Select course and enter question");
    const validOptions = pollOptions.filter(o => o.trim() !== "");
    if (validOptions.length < 2) return alert("Poll needs at least 2 options");

    try {
      await Updates.createPoll(selectedCourse, pollQuestion, validOptions.map(o => ({ option_text: o })));
      alert("Poll created!");
      setPollQuestion("");
      setPollOptions(["", ""]);
    } catch (err) {
      alert("Failed to create poll");
    }
  };

  const handleOptionChange = (idx: number, val: string) => {
    const newOptions = [...pollOptions];
    newOptions[idx] = val;
    setPollOptions(newOptions);
  };

  const addOption = () => setPollOptions([...pollOptions, ""]);
  const removeOption = (idx: number) => {
    if (pollOptions.length <= 2) return;
    const newOptions = pollOptions.filter((_, i) => i !== idx);
    setPollOptions(newOptions);
  };

  return (
    <div className="flex h-screen bg-theme-bg text-theme-text overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-theme-surface border-r border-theme-border flex flex-col">
        <div className="p-6 border-b border-theme-border">
          <div className="flex items-center gap-3 mb-2">
            <LayoutDashboard className="text-theme-accent" size={24} />
            <h1 className="text-xl font-bold tracking-tight">Admin Panel</h1>
          </div>
          <p className="text-xs text-theme-text-secondary opacity-60 uppercase font-bold tracking-widest">
            Control Center
          </p>
        </div>

        <nav className="flex-1 p-4 space-y-1 overflow-y-auto custom-scrollbar">
          <div className="pb-2 text-[10px] font-bold text-theme-text-secondary uppercase tracking-wider opacity-40 ml-2">
            User Management
          </div>
          <SidebarButton
            active={activeTab === "users"}
            onClick={() => setActiveTab("users")}
            icon={<Users size={18} />}
            label="Students"
          />
          <SidebarButton
            active={activeTab === "groups"}
            onClick={() => setActiveTab("groups")}
            icon={<FolderOpen size={18} />}
            label="Study Groups"
          />

          <div className="pt-4 pb-2 text-[10px] font-bold text-theme-text-secondary uppercase tracking-wider opacity-40 ml-2">
            Course Content
          </div>
          <SidebarButton
            active={activeTab === "syllabus"}
            onClick={() => { setActiveTab("syllabus"); if (selectedCourse) loadCourseSyllabus(); }}
            icon={<FileText size={18} />}
            label="Syllabus"
          />
          <SidebarButton
            active={activeTab === "materials"}
            onClick={() => { setActiveTab("materials"); if (selectedCourse) loadCourseFiles(); }}
            icon={<BookOpen size={18} />}
            label="Materials"
          />

          <div className="pt-4 pb-2 text-[10px] font-bold text-theme-text-secondary uppercase tracking-wider opacity-40 ml-2">
            Communication
          </div>
          <SidebarButton
            active={activeTab === "updates"}
            onClick={() => setActiveTab("updates")}
            icon={<BellRing size={18} />}
            label="Updates"
          />
          <SidebarButton
            active={activeTab === "polls"}
            onClick={() => setActiveTab("polls")}
            icon={<MessageSquare size={18} />}
            label="Polls"
          />
        </nav>

        <div className="p-4 border-t border-theme-border space-y-4">
          <div className="space-y-2">
            <div className="text-[10px] font-bold text-theme-text-secondary uppercase tracking-wider opacity-40 ml-2">
              Appearance
            </div>
            <div className="grid grid-cols-3 gap-1 bg-theme-bg/30 p-1 rounded-lg">
              <ThemeButton active={theme === 'emerald'} color="bg-emerald-500" onClick={() => setTheme('emerald')} />
              <ThemeButton active={theme === 'crimson'} color="bg-red-500" onClick={() => setTheme('crimson')} />
              <ThemeButton active={theme === 'cyber'} color="bg-fuchsia-500" onClick={() => setTheme('cyber')} />
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 py-2 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors border border-red-500/20 text-sm font-medium"
          >
            <LogOut size={16} />
            {cameFromStudentDashboard ? "Exit Portal" : "Logout"}
          </button>

          <div className="text-center pt-2">
            <span className="text-[10px] text-theme-text-secondary opacity-40">Admin ID: {adminId}</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden bg-theme-bg/50">
        {/* Top Header */}
        <header className="h-16 bg-theme-surface border-b border-theme-border flex items-center justify-between px-8 shrink-0">
          <div className="flex items-center gap-4">
            <div className="flex flex-col">
              <span className="text-xs text-theme-text-secondary opacity-60 font-medium">Selected Course</span>
              <select
                value={selectedCourse}
                onChange={(e) => setSelectedCourse(e.target.value)}
                className="bg-transparent border-none outline-none font-bold text-theme-accent p-0 cursor-pointer text-lg hover:text-theme-accent-hover transition-colors"
              >
                <option value="" className="bg-theme-surface">Select Course</option>
                {courses.map(c => <option key={c} value={c} className="bg-theme-surface">{c}</option>)}
              </select>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="text-right">
              <p className="text-[10px] text-theme-text-secondary uppercase font-bold tracking-widest opacity-40">Access Code</p>
              <p className="text-xl font-mono font-bold text-theme-text tracking-widest">{adminCode || "..."}</p>
            </div>
          </div>
        </header>

        {/* Dynamic Content */}
        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          <div className="max-w-5xl mx-auto space-y-6">
            {activeTab === "users" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <Card title="Create New Student" icon={<PlusCircle className="text-theme-accent" />}>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <InputField label="Username" value={newUser.username} onChange={(v: string) => setNewUser({ ...newUser, username: v })} placeholder="Enter name" />
                    <InputField label="Password" type="password" value={newUser.password} onChange={(v: string) => setNewUser({ ...newUser, password: v })} placeholder="••••••••" />
                    <InputField label="Course ID" value={newUser.course_id} onChange={(v: string) => setNewUser({ ...newUser, course_id: v })} placeholder="IT-101" />
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-theme-text-secondary uppercase tracking-wider opacity-60">Year</label>
                      <select
                        value={newUser.education_level}
                        onChange={(e) => setNewUser({ ...newUser, education_level: e.target.value })}
                        className="w-full px-4 h-10 rounded bg-theme-bg border border-theme-border outline-none focus:ring-1 focus:ring-theme-accent"
                      >
                        {["1", "2", "3", "4"].map((g) => <option key={g} value={g}>Year {g}</option>)}
                      </select>
                    </div>
                  </div>
                  <button onClick={createUser} className="w-full py-2.5 bg-theme-accent text-theme-bg rounded-lg hover:brightness-110 transition font-bold shadow-lg shadow-theme-accent/20">Register Student</button>
                </Card>

                <Card title="Existing Students" icon={<Users className="text-theme-accent" />}>
                  <div className="flex gap-2 mb-4">
                    <button onClick={loadCourseUsers} disabled={!selectedCourse} className="w-full py-2 border border-theme-border rounded-lg text-sm font-medium hover:bg-theme-accent/10 hover:border-theme-accent/50 transition-all disabled:opacity-30">
                      {selectedCourse ? `Load ${selectedCourse} Students` : "Select a course first"}
                    </button>
                  </div>
                  <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                    {courseUsers.length === 0 && <p className="text-center py-8 text-theme-text-secondary opacity-40 italic text-sm">No students loaded yet.</p>}
                    {courseUsers.map((u) => (
                      <div
                        key={u.id}
                        className={`p-3 rounded-xl border transition-all cursor-pointer group ${selectedUser === u.id ? 'bg-theme-accent/10 border-theme-accent' : 'bg-theme-bg/50 border-theme-border hover:border-theme-accent/40'}`}
                        onClick={() => loadUserGroups(u.id)}
                      >
                        <div className="flex justify-between items-center">
                          <div className="flex flex-col">
                            <span className="font-bold text-theme-text group-hover:text-theme-accent transition-colors">{u.username}</span>
                            <span className="text-[10px] text-theme-text-secondary opacity-40">DATABASE ID: {u.id}</span>
                          </div>
                          <ChevronRight size={16} className={`text-theme-accent transition-transform ${selectedUser === u.id ? 'rotate-90' : 'group-hover:translate-x-1'}`} />
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            )}

            {activeTab === "groups" && (
              selectedUser ? (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <div className="bg-theme-accent/10 border border-theme-accent/30 p-4 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FolderOpen className="text-theme-accent" size={24} />
                      <div>
                        <h3 className="font-bold text-theme-text">Groups for User #{selectedUser}</h3>
                        <p className="text-xs text-theme-text-secondary opacity-60">Managing specific study group memberships and files.</p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card title="Create/Select Group">
                      <div className="flex gap-2 mb-4">
                        <input
                          type="text"
                          placeholder="New Group Name"
                          value={groupName}
                          onChange={(e) => setGroupName(e.target.value)}
                          className="flex-1 h-10 px-4 rounded bg-theme-bg border border-theme-border outline-none focus:ring-1 focus:ring-theme-accent text-sm"
                        />
                        <button onClick={createGroup} className="px-6 bg-theme-accent text-theme-bg rounded-lg hover:brightness-110 transition font-bold text-sm">Create</button>
                      </div>
                      <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                        {userGroups.length === 0 && <p className="text-center py-8 text-theme-text-secondary opacity-40 italic text-sm">No groups found for this user.</p>}
                        {userGroups.map((g) => (
                          <div
                            key={g.id}
                            className={`p-3 rounded-xl border flex justify-between items-center cursor-pointer transition-all ${selectedGroup === g.id ? 'bg-theme-accent/10 border-theme-accent' : 'bg-theme-bg/50 border-theme-border hover:border-theme-accent/40'}`}
                            onClick={() => loadGroupFiles(g.id)}
                          >
                            <span className="font-bold text-sm">{g.group_name}</span>
                            <span className="text-[10px] text-theme-text-secondary opacity-40">GRP_ID: {g.id}</span>
                          </div>
                        ))}
                      </div>
                    </Card>

                    {selectedGroup && (
                      <Card title="Group Files" icon={<FolderOpen className="text-theme-accent" />}>
                        <div className="space-y-2 bg-theme-bg/30 p-3 rounded-xl min-h-[100px] mb-4">
                          {groupFiles.length === 0 && <p className="text-center py-4 text-theme-text-secondary opacity-40 italic text-xs">No files in this group.</p>}
                          {groupFiles.map(f => (
                            <div key={f.id} className="flex justify-between items-center text-xs p-2.5 hover:bg-theme-accent/5 rounded-lg border border-transparent hover:border-theme-accent/20 transition-all">
                              <span className="truncate flex-1 pr-4 font-medium">{f.file_name}</span>
                              <button onClick={(e) => { e.stopPropagation(); deleteFile(f.id); }} className="text-red-400 hover:bg-red-500/10 p-1.5 rounded-md transition-colors"><Trash2 size={14} /></button>
                            </div>
                          ))}
                        </div>
                        <div className="space-y-3 pt-2">
                          <input type="file" onChange={(e) => setFile(e.target.files?.[0])} className="text-[10px] text-theme-text-secondary block w-full file:mr-4 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-[10px] file:font-bold file:bg-theme-accent file:text-theme-bg hover:file:brightness-110 cursor-pointer" />
                          <button onClick={uploadFile} disabled={!file} className="w-full py-2 bg-theme-accent text-theme-bg rounded-lg hover:brightness-110 transition disabled:opacity-30 font-bold text-sm flex items-center justify-center gap-2">
                            <Upload size={16} />
                            Upload to Group
                          </button>
                        </div>
                      </Card>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-20 text-center animate-in fade-in zoom-in duration-500">
                  <div className="p-6 bg-theme-surface border border-theme-border rounded-full mb-6">
                    <Users size={48} className="text-theme-accent opacity-40" />
                  </div>
                  <h3 className="text-xl font-bold text-theme-text mb-2">No Student Selected</h3>
                  <p className="text-theme-text-secondary opacity-60 max-w-sm mb-8">
                    To manage study groups, please go to the <span className="text-theme-accent font-bold">Students</span> tab and select a specific student first.
                  </p>
                  <button
                    onClick={() => setActiveTab("users")}
                    className="px-8 py-3 bg-theme-accent text-theme-bg rounded-xl font-bold hover:brightness-110 transition-all shadow-lg shadow-theme-accent/20"
                  >
                    Go to Students Tab
                  </button>
                </div>
              )
            )}

            {activeTab === "syllabus" && (
              <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                <Card title="Syllabus Management" icon={<FileText className="text-theme-accent" />}>
                  <p className="text-sm text-theme-text-secondary opacity-60 mb-6">Format: Enter one topic or line item per line. This will be consumed by the AI to track progress.</p>
                  <textarea
                    value={courseSyllabus}
                    onChange={(e) => setCourseSyllabus(e.target.value)}
                    placeholder="Introduction to Programming\nVariables and Constants\nControl Flows..."
                    className="w-full h-96 px-4 py-4 rounded-xl bg-theme-bg border border-theme-border outline-none focus:ring-1 focus:ring-theme-accent resize-none font-mono text-sm leading-relaxed mb-6"
                  />
                  <div className="flex gap-4">
                    <button onClick={loadCourseSyllabus} disabled={!selectedCourse} className="flex-1 py-3 border border-theme-border rounded-xl font-bold hover:bg-theme-surface transition-colors disabled:opacity-30">Fetch Current</button>
                    <button onClick={saveCourseSyllabus} disabled={!selectedCourse} className="flex-1 py-3 bg-theme-accent text-theme-bg rounded-xl font-bold hover:brightness-110 transition-all disabled:opacity-30 shadow-lg shadow-theme-accent/20">Save Syllabus Changes</button>
                  </div>
                </Card>
              </div>
            )}

            {activeTab === "materials" && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="md:col-span-2">
                  <Card title="Current Course Materials" icon={<BookOpen className="text-theme-accent" />}>
                    <div className="grid grid-cols-1 gap-3 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
                      {courseFiles.length === 0 && (
                        <div className="text-center py-20 border-2 border-dashed border-theme-border rounded-2xl">
                          <BookOpen size={48} className="mx-auto text-theme-text-secondary opacity-20 mb-4" />
                          <p className="text-theme-text-secondary opacity-40 italic">No global materials found for {selectedCourse || "this course"}.</p>
                        </div>
                      )}
                      {courseFiles.map(f => (
                        <div key={f.id} className="bg-theme-bg/50 border border-theme-border p-4 rounded-xl flex items-center justify-between hover:border-theme-accent/30 transition-all group">
                          <div className="flex items-center gap-3">
                            <FileText className="text-theme-accent opacity-60" size={20} />
                            <span className="font-bold text-sm tracking-tight">{f.file_name}</span>
                          </div>
                          <button onClick={() => deleteFile(f.id, true)} className="text-red-400 hover:bg-red-500/10 p-2 rounded-lg transition-all opacity-0 group-hover:opacity-100">
                            <Trash2 size={18} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </Card>
                </div>
                <div className="md:col-span-1">
                  <Card title="Upload New">
                    <div className="flex flex-col gap-6">
                      <div className="p-6 border-2 border-dashed border-theme-border rounded-2xl text-center space-y-4">
                        <Upload size={32} className="mx-auto text-theme-accent opacity-40" />
                        <p className="text-xs text-theme-text-secondary leading-relaxed opacity-60">
                          Upload PDF or TXT files that will be accessible to ALL students enrolled in <span className="text-theme-accent font-bold">{selectedCourse || "the selected course"}</span>.
                        </p>
                        <input
                          type="file"
                          onChange={(e) => setCourseFile(e.target.files?.[0])}
                          className="hidden"
                          id="course-file-upload"
                        />
                        <label
                          htmlFor="course-file-upload"
                          className="block w-full py-2 bg-theme-surface border border-theme-border rounded-lg text-xs font-bold cursor-pointer hover:bg-theme-bg transition-colors"
                        >
                          {courseFile ? courseFile.name : "Browse Files"}
                        </label>
                      </div>
                      <button
                        onClick={uploadCourseFile}
                        disabled={!courseFile || !selectedCourse}
                        className="w-full py-3 bg-theme-accent text-theme-bg rounded-xl font-bold hover:brightness-110 shadow-lg shadow-theme-accent/20 disabled:opacity-30 transition-all"
                      >
                        Publish to Students
                      </button>
                    </div>
                  </Card>
                </div>
              </div>
            )}

            {activeTab === "updates" && (
              <div className="max-w-3xl mx-auto animate-in fade-in slide-in-from-bottom-2 duration-300">
                <Card title="Post Official Update" icon={<BellRing className="text-theme-accent" />}>
                  <div className="space-y-5">
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-theme-text-secondary uppercase tracking-wider opacity-60 ml-1">Update Content</label>
                      <textarea
                        value={updateContent}
                        onChange={(e) => setUpdateContent(e.target.value)}
                        placeholder="Write your announcement here..."
                        className="w-full h-40 px-4 py-4 rounded-xl bg-theme-bg border border-theme-border outline-none focus:ring-1 focus:ring-theme-accent resize-none text-sm leading-relaxed"
                      />
                    </div>
                    <InputField
                      label="Reference URL (Optional)"
                      value={updateUrl}
                      onChange={setUpdateUrl}
                      placeholder="https://example.com/more-info"
                      icon={<ExternalLink size={14} />}
                    />
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-theme-text-secondary uppercase tracking-wider opacity-60 ml-1">Attachment (The image itself)</label>
                      <div className="p-4 border border-theme-border bg-theme-bg rounded-xl flex items-center gap-4">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => setUpdateImageFile(e.target.files?.[0])}
                          className="text-xs text-theme-text-secondary file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-[10px] file:font-black file:bg-theme-accent file:text-theme-bg"
                        />
                      </div>
                    </div>
                    <button
                      onClick={handleUpdateSubmit}
                      disabled={!selectedCourse || !updateContent}
                      className="w-full py-4 bg-theme-accent text-theme-bg rounded-xl font-black uppercase tracking-widest text-sm hover:brightness-110 shadow-lg shadow-theme-accent/20 disabled:opacity-30 transition-all"
                    >
                      Broadcast Update
                    </button>
                  </div>
                </Card>
              </div>
            )}

            {activeTab === "polls" && (
              <div className="max-w-3xl mx-auto animate-in fade-in slide-in-from-bottom-2 duration-300">
                <Card title="Create New Poll" icon={<MessageSquare className="text-theme-accent" />}>
                  <div className="space-y-6">
                    <InputField
                      label="Poll Question"
                      value={pollQuestion}
                      onChange={setPollQuestion}
                      placeholder="What is your favorite topic?"
                    />
                    <div className="space-y-3">
                      <label className="text-xs font-bold text-theme-text-secondary uppercase tracking-wider opacity-60 ml-1">Options</label>
                      <div className="grid grid-cols-1 gap-3">
                        {pollOptions.map((opt, idx) => (
                          <div key={idx} className="flex gap-2 animate-in slide-in-from-right-2">
                            <input
                              type="text"
                              placeholder={`Option ${idx + 1}`}
                              value={opt}
                              onChange={(e) => handleOptionChange(idx, e.target.value)}
                              className="flex-1 px-4 h-12 rounded-xl bg-theme-bg border border-theme-border outline-none focus:ring-1 focus:ring-theme-accent text-sm font-medium"
                            />
                            {pollOptions.length > 2 && (
                              <button onClick={() => removeOption(idx)} className="w-12 h-12 flex items-center justify-center bg-red-500/10 text-red-400 rounded-xl hover:bg-red-500/20 transition-colors border border-red-500/20">
                                <Trash2 size={18} />
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                      <button onClick={addOption} className="text-xs font-bold text-theme-accent hover:text-theme-accent-hover transition-colors flex items-center gap-1.5 px-1">
                        <PlusCircle size={14} /> Add new option
                      </button>
                    </div>
                    <button
                      onClick={handlePollSubmit}
                      disabled={!selectedCourse || !pollQuestion}
                      className="w-full py-4 bg-theme-accent text-theme-bg rounded-xl font-black uppercase tracking-widest text-sm hover:brightness-110 shadow-lg shadow-theme-accent/20 disabled:opacity-30 transition-all"
                    >
                      Launch Poll
                    </button>
                  </div>
                </Card>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

// Sub-components
function SidebarButton({ active, onClick, icon, label, disabled }: any) {
  return (
    <button
      disabled={disabled}
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative ${active
        ? "bg-theme-accent/10 text-theme-accent border border-theme-accent/20 font-bold"
        : "text-theme-text-secondary opacity-60 hover:opacity-100 hover:bg-theme-bg/50 border border-transparent"
        } ${disabled ? "opacity-20 grayscale pointer-events-none" : ""}`}
    >
      {active && <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-6 bg-theme-accent rounded-r-full" />}
      <span className={active ? "text-theme-accent" : "group-hover:text-theme-accent transition-colors"}>{icon}</span>
      <span className="text-sm tracking-tight">{label}</span>
    </button>
  );
}

function ThemeButton({ active, color, onClick }: any) {
  return (
    <button
      onClick={onClick}
      className={`w-full h-8 rounded-md transition-all flex items-center justify-center ${color} ${active ? 'ring-2 ring-white scale-90 opacity-100' : 'opacity-40 hover:opacity-80 scale-75'}`}
    >
      {active && <CheckCircle2 size={12} className="text-white" />}
    </button>
  );
}

function Card({ title, icon, children }: { title: string, icon?: React.ReactNode, children: React.ReactNode }) {
  return (
    <div className="bg-theme-surface border border-theme-border rounded-2xl p-6 shadow-xl shadow-black/20 flex flex-col h-full">
      <div className="flex items-center gap-3 mb-6">
        {icon}
        <h2 className="text-lg font-bold tracking-tight text-theme-text">{title}</h2>
      </div>
      <div className="flex-1">{children}</div>
    </div>
  );
}

interface InputFieldProps {
  label: string;
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  type?: string;
  icon?: React.ReactNode;
}

function InputField({ label, value, onChange, placeholder, type = "text", icon }: InputFieldProps) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <label className="text-xs font-bold text-theme-text-secondary uppercase tracking-wider opacity-60 ml-1">{label}</label>
        {icon}
      </div>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-4 h-11 rounded-xl bg-theme-bg border border-theme-border outline-none focus:ring-1 focus:ring-theme-accent text-sm"
      />
    </div>
  );
}
