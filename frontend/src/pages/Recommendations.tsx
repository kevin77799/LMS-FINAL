import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Analysis, Recs as RecsApi } from "@/api/endpoints";

interface YoutubeResult {
  id: string;
  title: string;
}

interface AnalysisStatus {
  has_report: boolean;
  has_syllabus: boolean;
}

export default function Recommendations() {
  const nav = useNavigate();
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  const [groupId, setGroupId] = useState<number | null>(
    Number(localStorage.getItem("group_id")) || null
  );
  const [status, setStatus] = useState<AnalysisStatus | null>(null);
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  const [topic, setTopic] = useState(localStorage.getItem("search_topic") || "");
  const [youtubeResults, setYoutubeResults] = useState<YoutubeResult[]>(
    JSON.parse(localStorage.getItem("youtube_results") || "[]")
  );
  const [webResults, setWebResults] = useState<string[]>(
    JSON.parse(localStorage.getItem("web_results") || "[]")
  );

  useEffect(() => {
    if (groupId) localStorage.setItem("group_id", String(groupId));
    localStorage.setItem("search_topic", topic);
    localStorage.setItem("youtube_results", JSON.stringify(youtubeResults));
    localStorage.setItem("web_results", JSON.stringify(webResults));
  }, [groupId, topic, youtubeResults, webResults]);

  useEffect(() => {
    const fetchStatus = async () => {
      if (!groupId) return setStatus(null);
      try {
        const s = await Analysis.getStatus(groupId);
        setStatus(s);
      } catch {
        setStatus(null);
      }
    };
    fetchStatus();
  }, [groupId]);

  const handleGenerateAnalysis = async () => {
    if (!groupId) return alert("Select Group ID first.");
    setIsLoadingAnalysis(true);
    try {
      await Analysis.run(groupId);
      const s = await Analysis.getStatus(groupId);
      setStatus(s);
      alert("Analysis generated successfully! Check the Dashboard.");
    } catch (err) {
      console.error(err);
      alert("Error generating analysis.");
    } finally {
      setIsLoadingAnalysis(false);
    }
  };

  const handleSearch = async () => {
    if (!topic) return;
    setIsSearching(true);
    try {
      const [yt, web] = await Promise.all([
        RecsApi.youtube(topic).catch(() => []),
        RecsApi.web(topic).catch(() => [])
      ]);
      setYoutubeResults(yt || []);
      setWebResults(web || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  if (!user?.username) nav("/login");

  const canGenerate = status?.has_report && status?.has_syllabus;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-6 text-theme-accent">Recommendations</h1>

      {/* Analysis Section */}
      <div className="p-6 bg-theme-surface border border-theme-border rounded-md space-y-4">
        <h2 className="text-lg font-semibold text-theme-text">Generate Full Analysis</h2>
        <input
          type="number"
          placeholder="Group ID"
          value={groupId ?? ""}
          onChange={(e) => setGroupId(Number(e.target.value))}
          className="w-full px-3 py-2 rounded-md bg-theme-bg border border-theme-border focus:outline-none text-theme-text"
        />
        <button
          onClick={handleGenerateAnalysis}
          disabled={!canGenerate || isLoadingAnalysis}
          className="px-4 py-2 bg-theme-accent text-theme-bg rounded-md hover:bg-theme-accent-hover transition disabled:opacity-50"
        >
          {isLoadingAnalysis ? "Generating..." : "Generate Analysis & Recommendations"}
        </button>
      </div>

      {/* Search Section */}
      <div className="p-6 bg-theme-surface border border-theme-border rounded-md">
        <h2 className="text-lg font-semibold mb-2 text-theme-text">Find Additional Resources</h2>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            placeholder="Topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="flex-1 px-3 py-2 rounded-md bg-theme-bg border border-theme-border focus:outline-none text-theme-text"
          />
          <button
            onClick={handleSearch}
            disabled={isSearching}
            className="px-4 py-2 bg-theme-accent text-theme-bg rounded-md hover:bg-theme-accent-hover transition disabled:opacity-50"
          >
            {isSearching ? "Searching..." : "Search"}
          </button>
        </div>

        {/* Results */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {youtubeResults.length > 0 && (
            <div>
              <h3 className="font-semibold mb-2">YouTube</h3>
              <ul className="list-disc pl-6 space-y-1">
                {youtubeResults.map((v) => (
                  <li key={v.id}>
                    <a href={`https://www.youtube.com/watch?v=${v.id}`} target="_blank" rel="noreferrer" className="text-theme-accent hover:underline">
                      {v.title}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {webResults.length > 0 && (
            <div>
              <h3 className="font-semibold mb-2">Web</h3>
              <ul className="list-disc pl-6 space-y-1">
                {webResults.map((url, i) => (
                  <li key={i}>
                    <a href={url} target="_blank" rel="noreferrer" className="text-theme-text-secondary hover:underline break-all">
                      {url}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
