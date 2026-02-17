import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Syllabus as SyllabusApi, Groups as GroupsApi } from "@/api/endpoints";

type Ratings = Record<string, number>;
interface Group {
  id: number;
  group_name: string;
}

export default function Syllabus() {
  const nav = useNavigate();
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  const [activeGroupId, setActiveGroupId] = useState<number | null>(
    Number(localStorage.getItem("group_id")) || null
  );
  const [userGroups, setUserGroups] = useState<Group[]>([]);
  const [syllabusContent, setSyllabusContent] = useState("");
  const [topics, setTopics] = useState<string[]>([]);
  const [ratings, setRatings] = useState<Ratings>({});
  const [isLoading, setIsLoading] = useState(false);

  // Sync group_id to localStorage
  useEffect(() => {
    if (activeGroupId) {
      localStorage.setItem("group_id", String(activeGroupId));
    }
  }, [activeGroupId]);

  useEffect(() => {
    if (!user?.username) {
      nav("/login");
      return;
    }

    const fetchGroups = async () => {
      try {
        const groups = await GroupsApi.list(user.user_id);
        setUserGroups(groups);
        if (!activeGroupId && groups.length > 0) {
          setActiveGroupId(groups[0].id);
        }
      } catch (err) {
        console.error("Failed to fetch groups:", err);
      }
    };
    fetchGroups();
  }, [user.user_id, nav]);

  useEffect(() => {
    const loadSyllabus = async () => {
      if (!user?.course_id && !activeGroupId) return;

      setIsLoading(true);
      try {
        let content = "";
        let savedRatings: Ratings = {};

        // 1. Get Course Syllabus
        if (user?.course_id) {
          const courseData = await SyllabusApi.getCourse(user.course_id);
          content = courseData?.syllabus_content || "";
        }

        // 2. Get Group Overrides (Ratings)
        if (activeGroupId) {
          try {
            const groupData = await SyllabusApi.getGroup(activeGroupId);
            if (groupData?.syllabus_content) {
              content = groupData.syllabus_content;
            }
            if (groupData?.ratings) {
              savedRatings = groupData.ratings;
            }
          } catch (e) {
            console.warn("Group syllabus load failed", e);
          }
        }

        setSyllabusContent(content);

        const parsedTopics: string[] = content
          .split("\n")
          .map(t => t.trim())
          .filter(t => t !== "");

        setTopics(parsedTopics);

        const mergedRatings: Ratings = {};
        parsedTopics.forEach(t => {
          mergedRatings[t] = savedRatings[t] !== undefined ? savedRatings[t] : 5;
        });

        setRatings(mergedRatings);

      } catch (err) {
        console.error("Error loading syllabus:", err);
        setSyllabusContent("");
      } finally {
        setIsLoading(false);
      }
    };

    loadSyllabus();
  }, [user?.course_id, activeGroupId]);

  const handleRatingChange = (topic: string, value: number) => {
    setRatings(prev => ({ ...prev, [topic]: value }));
  };

  const saveSyllabus = async () => {
    if (!activeGroupId) return;
    setIsLoading(true);
    try {
      await SyllabusApi.saveGroup(activeGroupId, syllabusContent, ratings);
      alert("Syllabus saved successfully!");
    } catch (err) {
      console.error(err);
      alert("Error saving syllabus.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-4 text-theme-accent">Syllabus</h1>

      <div className="mb-4">
        <label className="mr-2">Select Group:</label>
        <select
          className="bg-theme-surface border border-theme-border px-2 py-1 rounded-md text-theme-text outline-none"
          value={activeGroupId || ""}
          onChange={(e) => setActiveGroupId(Number(e.target.value))}
        >
          <option value="" disabled>-- Select a Group --</option>
          {userGroups.map(g => (
            <option key={g.id} value={g.id}>{g.group_name} (ID: {g.id})</option>
          ))}
        </select>
      </div>

      {isLoading && <p>Loading syllabus...</p>}

      {!isLoading && topics.length > 0 && (
        <div className="space-y-6">
          {topics.map((topic, idx) => (
            <div key={idx} className="p-4 border border-theme-border rounded-md bg-theme-surface">
              <p className="font-medium mb-1">{topic}</p>
              <input
                type="range"
                min={1}
                max={10}
                value={ratings[topic] || 5}
                onChange={(e) => handleRatingChange(topic, Number(e.target.value))}
                className="w-full accent-theme-accent"
              />
              <p className="text-theme-accent text-sm">Rating: {ratings[topic] || 5}</p>
            </div>
          ))}
          <button
            onClick={saveSyllabus}
            disabled={isLoading || !activeGroupId}
            className="px-4 py-2 border border-theme-border rounded-md hover:bg-theme-text hover:text-theme-bg transition"
          >
            {isLoading ? "Saving..." : "Save Syllabus for Selected Group"}
          </button>
        </div>
      )}

      {!isLoading && topics.length === 0 && <p className="text-theme-text-secondary">No syllabus available for this course.</p>}
    </div>
  );
}
