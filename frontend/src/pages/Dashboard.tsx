import { useEffect, useState } from "react";
import { useNavigate, NavLink } from "react-router-dom";
import { Analysis, Admin, Updates } from "@/api/endpoints";
import { ChevronLeft, ChevronRight, CheckCircle2, MapPin, Milestone, Goal, ListChecks, Trophy, Bell, ExternalLink, X, Maximize2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from 'remark-gfm';

const RoadmapVisual = ({ markdown }: { markdown: string }) => {
  const parseRoadmap = (text: string) => {
    const steps = [];
    const regex = /Step\s+(\d+):\s*([^\n]+)([\s\S]*?)(?=Step\s+\d+:|$)/g;
    let match;
    while ((match = regex.exec(text)) !== null) {
      const [_, number, title, content] = match;
      steps.push({ number, title, content: stripIndentation(content) });
    }
    return steps;
  };

  const stripIndentation = (text: string) => {
    const lines = text.split('\n');
    // Find minimum indentation of non-empty lines
    let minIndent = Infinity;
    for (const line of lines) {
      if (line.trim()) {
        const match = line.match(/^(\s*)/);
        if (match) {
          minIndent = Math.min(minIndent, match[1].length);
        }
      }
    }
    if (minIndent === Infinity) return text;

    return lines.map(line => {
      if (line.trim()) {
        return line.slice(minIndent);
      }
      return line;
    }).join('\n');
  };

  const steps = parseRoadmap(markdown);

  if (!steps || steps.length === 0) {
    return (
      <div className="border border-theme-surface p-4 rounded-lg bg-theme-surface">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ node, ...props }: any) => <h1 className="text-2xl font-bold mb-4 text-theme-accent" {...props} />,
            h2: ({ node, ...props }: any) => <h2 className="text-xl font-semibold mb-3 text-theme-accent" {...props} />,
            h3: ({ node, ...props }: any) => <h3 className="text-lg font-medium mb-2 text-theme-text-secondary" {...props} />,
            ul: ({ node, ...props }: any) => <ul className="list-disc list-inside space-y-1 ml-4" {...props} />,
            ol: ({ node, ...props }: any) => <ol className="list-decimal list-inside space-y-1 ml-4" {...props} />,
            p: ({ node, ...props }: any) => <p className="mb-4 leading-relaxed" {...props} />,
          }}
        >
          {markdown}
        </ReactMarkdown>
      </div>
    );
  }

  return (
    <div className="relative border-l-2 border-theme-accent/30 ml-4 space-y-10 my-8">
      {steps.map((step, idx) => (
        <div key={idx} className="relative pl-8 group">
          {/* Timeline Node */}
          <div className="absolute -left-[11px] top-0 bg-theme-bg text-theme-accent ring-4 ring-theme-bg">
            <CheckCircle2 size={24} className="fill-theme-surface" />
          </div>

          {/* Card */}
          <div className="bg-theme-surface rounded-xl border border-theme-border p-6 shadow-lg hover:border-theme-accent/50 transition-all duration-300 hover:transform hover:translate-x-1">
            <div className="flex items-center gap-3 mb-4 border-b border-theme-border pb-3">
              <span className="bg-theme-accent/10 text-theme-accent px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase">
                Step {step.number}
              </span>
              <h4 className="text-lg font-bold text-theme-text">{step.title}</h4>
            </div>

            <div className="prose prose-invert prose-sm max-w-none text-gray-300 break-words whitespace-pre-wrap">
              {/* Detect sections inside content for icons */}
              {step.content.split('\n').map((line, i) => {
                const trimmed = line.trim();
                // Check if line starts with key headers, allowing for bolding and bullets
                const isObjective = /^[\*\-]?\s*(\*\*)?Objective:?(\*\*)?/.test(trimmed);
                const isActions = /^[\*\-]?\s*(\*\*)?Actions:?(\*\*)?/.test(trimmed);
                const isDeliverables = /^[\*\-]?\s*(\*\*)?Key Deliverables:?(\*\*)?/.test(trimmed);

                if (isObjective) {
                  const content = trimmed.replace(/^[\*\-]?\s*(\*\*)?Objective:?(\*\*)?/, '').trim();
                  return (
                    <div key={i} className="flex gap-2 items-start mt-3 mb-2">
                      <Goal size={16} className="text-blue-400 mt-1 shrink-0" />
                      <p className="m-0"><span className="text-blue-400 font-semibold">Objective:</span> {content}</p>
                    </div>
                  );
                }
                if (isActions) {
                  return (
                    <div key={i} className="flex gap-2 items-start mt-3 mb-2">
                      <ListChecks size={16} className="text-green-400 mt-1 shrink-0" />
                      <p className="m-0 font-semibold text-green-400">Actions:</p>
                    </div>
                  );
                }
                if (isDeliverables) {
                  const content = trimmed.replace(/^[\*\-]?\s*(\*\*)?Key Deliverables:?(\*\*)?/, '').trim();
                  return (
                    <div key={i} className="flex gap-2 items-start mt-3 mb-2 bg-gray-800/30 p-2 rounded border border-gray-700/50">
                      <Trophy size={16} className="text-yellow-400 mt-1 shrink-0" />
                      <p className="m-0"><span className="text-yellow-400 font-semibold">Deliverables:</span> {content}</p>
                    </div>
                  );
                }
                // Default rendering: Render the trimmed line to avoid code block interpretation from indentation
                // We use a fragment to render standard markdown elements like list items properly if they exist in the trimmed line
                return <ReactMarkdown key={i} remarkPlugins={[remarkGfm]} components={{ p: ({ node, ...props }: any) => <p className="mb-1" {...props} /> }}>{trimmed}</ReactMarkdown>;
              })}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default function Dashboard() {
  const nav = useNavigate();
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const [groupId, setGroupId] = useState<number | null>(
    Number(localStorage.getItem("group_id")) || null
  );
  const [data, setData] = useState<{
    analysis?: string;
    timetable?: string;
    roadmap?: string;
    timestamp?: string;
  }>({});
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (groupId) localStorage.setItem("group_id", String(groupId));
  }, [groupId]);

  const loadAnalysis = async () => {
    if (!groupId) return;
    setIsLoading(true);
    try {
      const res = await Analysis.getLatest(groupId);
      setData(res || {});
    } catch (error) {
      console.error("Failed to load analysis:", error);
      setData({});
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (groupId) loadAnalysis();
  }, [groupId]);

  // Load Course Files
  const [courseFiles, setCourseFiles] = useState<any[]>([]);
  useEffect(() => {
    if (user.course_id) {
      Admin.listCourseFiles(user.course_id)
        .then(setCourseFiles)
        .catch(err => console.error("Failed to load course files", err));
    }
  }, [user.course_id]);

  // Updates & Notifications
  const [updates, setUpdates] = useState<any[]>([]);
  const [hasNewUpdates, setHasNewUpdates] = useState(false);

  const loadUpdates = async () => {
    if (!user.course_id) return;
    try {
      const list = await Updates.list(user.course_id, user.id);
      setUpdates(list);

      if (list.length > 0) {
        const lastSeen = localStorage.getItem(`last_seen_update_${user.course_id}`);
        const latestDate = list[0].created_at;
        if (!lastSeen || new Date(latestDate) > new Date(lastSeen)) {
          setHasNewUpdates(true);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const markUpdatesAsSeen = () => {
    if (updates.length > 0) {
      localStorage.setItem(`last_seen_update_${user.course_id}`, updates[0].created_at);
      setHasNewUpdates(false);
    }
  };

  const handleVote = async (pollId: number, optionId: number) => {
    try {
      await Updates.vote(user.id, optionId);
      await loadUpdates(); // Reload to show results
    } catch (err) {
      alert("Vote failed or already voted");
    }
  };

  useEffect(() => {
    if (user.course_id) loadUpdates();
  }, [user.course_id]);

  // Image Popup State
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold mb-4 text-theme-accent">Dashboard</h1>

      {/* Group ID + Refresh */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <input
            placeholder="Group ID"
            type="number"
            value={groupId ?? ""}
            onChange={(e) => setGroupId(Number(e.target.value))}
            className="px-3 py-2 rounded-md bg-theme-surface border border-theme-border outline-none"
          />
          <button
            onClick={loadAnalysis}
            disabled={isLoading}
            className="border border-white text-white px-3 py-1 rounded-md text-sm font-medium hover:bg-white hover:text-black transition duration-200"
          >
            {isLoading ? "Loading..." : "Refresh"}
          </button>
        </div>
        <div className="text-right">
          <span className="text-xs text-gray-400 block">Enrolled Course</span>
          <span className="text-xl font-bold text-theme-accent">{user.course_id || "N/A"}</span>
        </div>
      </div>

      {/* Course Materials Section */}
      {courseFiles.length > 0 && (
        <div className="bg-theme-surface border border-theme-border p-4 rounded-lg shadow-lg mb-6">
          <h3 className="text-lg font-semibold text-theme-accent mb-3 flex items-center gap-2">
            <Milestone size={20} />
            Class Materials ({user.course_id})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {courseFiles.map((f: any) => (
              <a
                key={f.id}
                href={`/api/admin/courses/files/${f.id}/download`}
                target="_blank"
                rel="noreferrer"
                title="Download material"
                className="flex items-center gap-3 p-3 rounded bg-theme-bg border border-theme-border hover:border-theme-accent/50 transition group"
              >
                <div className="bg-theme-accent/10 p-2 rounded group-hover:bg-theme-accent/20">
                  <ListChecks size={18} className="text-theme-accent" />
                </div>
                <div className="overflow-hidden">
                  <p className="text-sm font-medium text-theme-text truncate">{f.file_name}</p>
                  <p className="text-xs text-theme-text-secondary">{new Date(f.uploaded_at).toLocaleDateString()}</p>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Updates & Notifications Section */}
      <div className="bg-theme-surface border border-theme-border p-4 rounded-lg shadow-lg mb-6 relative">
        {hasNewUpdates && (
          <span className="absolute -top-1 -right-1 bg-red-500 w-3 h-3 rounded-full animate-pulse ring-2 ring-theme-bg"></span>
        )}
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-theme-accent flex items-center gap-2">
            <Bell size={20} />
            Updates & Notifications
          </h3>
          {hasNewUpdates && (
            <button onClick={markUpdatesAsSeen} className="text-xs text-indigo-400 hover:text-indigo-300">
              Mark as Read
            </button>
          )}
        </div>

        <div className="space-y-4 max-h-96 overflow-y-auto custom-scrollbar pr-2">
          {updates.length === 0 && <p className="text-sm text-gray-400 italic">No updates yet.</p>}
          {updates.map((item: any) => (
            <div key={item.id} className="bg-theme-bg p-4 rounded border border-theme-border/50">
              <div className="flex justify-between items-start mb-2">
                <span className={`text-xs px-2 py-0.5 rounded font-bold uppercase ${item.type === 'poll' ? 'bg-purple-500/20 text-purple-400' : 'bg-blue-500/20 text-blue-400'}`}>
                  {item.type}
                </span>
                <span className="text-xs text-gray-500">{new Date(item.created_at).toLocaleDateString()}</span>
              </div>

              {item.type === 'update' ? (
                <div className="prose prose-invert prose-sm">
                  {/* 1. Description */}
                  <p className="whitespace-pre-wrap text-theme-text">{item.content}</p>

                  {/* 2. Image (JPEG/IMG itself) */}
                  {item.image_url && (
                    <div className="mt-3 rounded-lg overflow-hidden border border-theme-border relative group/img cursor-pointer" onClick={() => setSelectedImage(item.image_url)}>
                      <img
                        src={item.image_url}
                        alt="Update attachment"
                        className="w-full h-auto object-cover max-h-[300px] transition-all duration-500 group-hover/img:scale-110 group-hover/img:brightness-75"
                        onError={(e) => (e.currentTarget.style.display = 'none')}
                      />
                      <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover/img:opacity-100 transition-opacity duration-300 bg-black/40">
                        <div className="flex flex-col items-center gap-2">
                          <Maximize2 className="text-white animate-pulse" size={24} />
                          <span className="text-white text-xs font-bold uppercase tracking-wider">Click to expand</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 3. External URL (Link) */}
                  {item.external_url && (
                    <a
                      href={item.external_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-theme-accent/10 border border-theme-accent/30 rounded-lg text-theme-accent text-xs font-bold hover:bg-theme-accent/20 transition-all shadow-sm"
                    >
                      <ExternalLink size={14} />
                      View Full Resource
                    </a>
                  )}
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="font-semibold text-lg">{item.question}</p>
                  <div className="space-y-2">
                    {item.options.map((opt: any) => {
                      const totalVotes = item.options.reduce((acc: number, o: any) => acc + o.votes, 0);
                      const percent = totalVotes > 0 ? (opt.votes / totalVotes) * 100 : 0;
                      const isVoted = item.user_voted_option_id === opt.id;
                      const hasVotedAny = item.user_voted_option_id !== null;

                      return (
                        <div key={opt.id} className="relative">
                          <button
                            disabled={hasVotedAny}
                            onClick={() => handleVote(item.id, opt.id)}
                            className={`w-full text-left p-3 rounded border transition relative overflow-hidden ${isVoted ? 'border-green-500 bg-green-500/10' : 'border-gray-700 bg-[#2a2d35] hover:bg-[#343842] disabled:hover:bg-[#2a2d35] disabled:cursor-default'}`}
                          >
                            <div className="relative z-10 flex justify-between">
                              <span>{opt.text}</span>
                              {hasVotedAny && <span className="text-sm font-mono">{Math.round(percent)}%</span>}
                            </div>
                            {hasVotedAny && (
                              <div
                                className={`absolute top-0 left-0 h-full transition-all duration-500 ${isVoted ? 'bg-green-500/20' : 'bg-gray-600/20'}`}
                                style={{ width: `${percent}%` }}
                              ></div>
                            )}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                  <p className="text-xs text-gray-500 text-right">
                    {item.options.reduce((acc: number, o: any) => acc + o.votes, 0)} votes
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {isLoading && (
        <p className="mt-4 text-gray-300">Loading analysis report...</p>
      )}

      {!isLoading && data?.analysis ? (
        <>
          <h3 className="text-lg font-semibold mt-4">Latest Analysis</h3>
          <div className="border border-theme-border p-4 rounded-lg bg-theme-surface">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ node, ...props }: any) => <h1 className="text-2xl font-bold mb-4 text-theme-accent" {...props} />,
                h2: ({ node, ...props }: any) => <h2 className="text-xl font-semibold mb-3 text-theme-accent" {...props} />,
                h3: ({ node, ...props }: any) => <h3 className="text-lg font-medium mb-2 text-theme-text-secondary" {...props} />,
                ul: ({ node, ...props }: any) => <ul className="list-disc list-inside space-y-1 ml-4" {...props} />,
                ol: ({ node, ...props }: any) => <ol className="list-decimal list-inside space-y-1 ml-4" {...props} />,
                p: ({ node, ...props }: any) => <p className="mb-4 leading-relaxed" {...props} />,

                table: ({ node, ...props }: any) => (
                  <div className="overflow-x-auto my-6 rounded-lg border border-theme-border shadow-xl">
                    <table className="min-w-full divide-y divide-theme-border bg-theme-bg" {...props} />
                  </div>
                ),
                thead: ({ node, ...props }: any) => (
                  <thead className="bg-theme-surface" {...props} />
                ),
                tbody: ({ node, ...props }: any) => (
                  <tbody className="divide-y divide-theme-border bg-theme-surface" {...props} />
                ),
                tr: ({ node, ...props }: any) => (
                  <tr className="hover:bg-theme-bg/50 transition-colors duration-150" {...props} />
                ),
                th: ({ node, ...props }: any) => (
                  <th className="px-6 py-4 text-left text-xs font-bold text-theme-text uppercase tracking-wider border-b border-theme-border" {...props} />
                ),
                td: ({ node, ...props }: any) => (
                  <td className="px-6 py-4 whitespace-normal text-sm text-theme-text-secondary border-r border-theme-border/50 last:border-r-0 leading-snug" {...props} />
                ),
              }}
            >
              {data.analysis}
            </ReactMarkdown>
          </div>

          <h3 className="text-lg font-semibold mt-4">Timetable</h3>
          <div className="border border-theme-border p-4 rounded-lg bg-theme-surface">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                table: ({ node, ...props }: any) => (
                  <div className="overflow-x-auto my-6 rounded-lg border border-theme-border shadow-xl">
                    <table className="min-w-full divide-y divide-theme-border bg-theme-bg" {...props} />
                  </div>
                ),
                thead: ({ node, ...props }: any) => (
                  <thead className="bg-theme-surface" {...props} />
                ),
                tbody: ({ node, ...props }: any) => (
                  <tbody className="divide-y divide-theme-border bg-theme-surface" {...props} />
                ),
                tr: ({ node, ...props }: any) => (
                  <tr className="hover:bg-theme-bg/50 transition-colors duration-150" {...props} />
                ),
                th: ({ node, ...props }: any) => (
                  <th className="px-6 py-4 text-left text-xs font-bold text-theme-text uppercase tracking-wider border-b border-theme-border" {...props} />
                ),
                td: ({ node, ...props }: any) => (
                  <td className="px-6 py-4 whitespace-normal text-sm text-theme-text-secondary border-r border-theme-border/50 last:border-r-0 leading-snug" {...props} />
                ),
              }}
            >
              {data.timetable}
            </ReactMarkdown>
          </div>

          <h3 className="text-lg font-semibold mt-4">Roadmap</h3>
          {data.roadmap && <RoadmapVisual markdown={data.roadmap} />}

          <small className="block mt-6 text-gray-400">
            Last updated: {data.timestamp}
          </small>
        </>
      ) : (
        !isLoading &&
        groupId && (
          <div className="bg-yellow-800 text-yellow-200 px-4 py-2 rounded-md mt-4">
            No analysis found for this group. Please generate one from the
            "Recommendations" tab.
          </div>
        )
      )}

      {/* Image Popup Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 z-[9999] flex items-center justify-center p-4 md:p-10 transition-all duration-300 backdrop-blur-md bg-black/90"
          onClick={() => setSelectedImage(null)}
        >
          <button
            className="absolute top-6 right-6 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white transition-all transform hover:scale-110 active:scale-95"
            onClick={() => setSelectedImage(null)}
          >
            <X size={28} />
          </button>

          <div className="relative max-w-full max-h-full flex items-center justify-center shadow-2xl rounded-lg overflow-hidden border border-white/10">
            <img
              src={selectedImage}
              alt="Expanded view"
              className="max-w-full max-h-[90vh] object-contain shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            />
          </div>

          <div className="absolute bottom-6 left-0 right-0 text-center pointer-events-none">
            <p className="text-white/60 text-sm font-medium tracking-wide">Press anywhere or use the close button to return</p>
          </div>
        </div>
      )}
    </div>
  );
}
