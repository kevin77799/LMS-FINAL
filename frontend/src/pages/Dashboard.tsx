import { useEffect, useState } from "react";
import { useNavigate, NavLink } from "react-router-dom";
import { Analysis } from "@/api/endpoints";
import { ChevronLeft, ChevronRight, CheckCircle2, MapPin, Milestone, Goal, ListChecks, Trophy } from "lucide-react";
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

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold mb-4 text-theme-accent">Dashboard</h1>

      {/* Group ID + Refresh */}
      <div className="mb-6 flex items-center gap-2">
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
    </div>
  );
}
