import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Quiz as Q } from "@/api/endpoints";

interface QuizData {
  subject: string;
  questions: string[];
  options: string[][];
  answers: string[];
  explanations: string[];
}

interface GradedResults {
  marks: number[];
  tot_mark: number;
}

export default function Quiz() {
  const nav = useNavigate();
  const [user, setUser] = useState<{ user_id: number; username: string } | null>(null);

  const [groupId, setGroupId] = useState<number | null>(
    Number(localStorage.getItem("group_id")) || null
  );

  const [subject, setSubject] = useState(localStorage.getItem("quiz_subject") || "");
  const [quiz, setQuiz] = useState<QuizData | null>(
    JSON.parse(localStorage.getItem("active_quiz") || "null")
  );
  const [userAnswers, setUserAnswers] = useState<string[]>(
    JSON.parse(localStorage.getItem("user_answers") || "[]")
  );
  const [gradedResults, setGradedResults] = useState<GradedResults | null>(
    JSON.parse(localStorage.getItem("graded_results") || "null")
  );
  const [isSubmitted, setIsSubmitted] = useState(
    localStorage.getItem("quiz_submitted") === "true"
  );
  const [isLoading, setIsLoading] = useState(false);

  // Sync state to localStorage
  useEffect(() => {
    if (groupId) localStorage.setItem("group_id", String(groupId));
    localStorage.setItem("quiz_subject", subject);
    localStorage.setItem("active_quiz", JSON.stringify(quiz));
    localStorage.setItem("user_answers", JSON.stringify(userAnswers));
    localStorage.setItem("graded_results", JSON.stringify(gradedResults));
    localStorage.setItem("quiz_submitted", String(isSubmitted));
  }, [groupId, subject, quiz, userAnswers, gradedResults, isSubmitted]);

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) setUser(JSON.parse(storedUser));
    else nav("/login");
  }, [nav]);

  const handleGenerateQuiz = async () => {
    if (!groupId || !subject) return alert("Provide Group ID and Subject.");
    setIsLoading(true);
    setQuiz(null);
    setUserAnswers([]);
    setGradedResults(null);
    setIsSubmitted(false);

    try {
      const q = await Q.generate(groupId, subject);
      setQuiz(q);
      setUserAnswers(new Array(q.questions.length).fill(""));
    } catch (err) {
      console.error(err);
      alert("Failed to generate quiz.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmitQuiz = async () => {
    if (!quiz || !user) return;
    try {
      const res = await Q.grade(quiz.answers, userAnswers);
      setGradedResults(res);
      setIsSubmitted(true);
      await Q.save(groupId!, user.user_id, {
        subject,
        questions: quiz.questions,
        options: quiz.options,
        correct_answers: quiz.answers,
        user_answers: userAnswers,
        marks: res.marks,
        explanations: quiz.explanations,
        related_content: [],
        related_videos: [],
      });
    } catch (err) {
      console.error(err);
      alert("Error submitting quiz.");
    }
  };

  const handleAnswerChange = (qIndex: number, ans: string) => {
    const copy = [...userAnswers];
    copy[qIndex] = ans;
    setUserAnswers(copy);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold mb-6 text-theme-accent">Quiz</h1>

      {/* Input Section */}
      <div className="flex gap-3 mb-6">
        <input
          type="number"
          placeholder="Group ID"
          value={groupId ?? ""}
          onChange={(e) => setGroupId(Number(e.target.value))}
          className="flex-1 px-3 py-2 bg-theme-surface border border-theme-border rounded-md focus:outline-none text-theme-text"
        />
        <input
          placeholder="Subject"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          className="flex-1 px-3 py-2 bg-theme-surface border border-theme-border rounded-md focus:outline-none text-theme-text"
        />
        <button
          onClick={handleGenerateQuiz}
          disabled={isLoading}
          className="px-4 py-2 bg-theme-accent text-theme-bg rounded-md hover:bg-theme-accent-hover transition"
        >
          {isLoading ? "Generating..." : "Generate"}
        </button>
      </div>

      {/* Quiz */}
      {quiz && quiz.questions.map((q, i) => (
        <div key={i} className="p-4 mb-4 border border-theme-border rounded-md bg-theme-surface">
          <p className="font-semibold mb-2">Q{i + 1}: {q}</p>
          <div className="space-y-2">
            {quiz.options[i].map((opt, j) => (
              <label key={j} className="flex items-center gap-2">
                <input
                  type="radio"
                  name={`q${i}`}
                  value={opt}
                  checked={userAnswers[i] === opt}
                  disabled={isSubmitted}
                  onChange={() => handleAnswerChange(i, opt)}
                  className="accent-theme-accent"
                />
                <span>{opt}</span>
              </label>
            ))}
          </div>
        </div>
      ))}

      {!isSubmitted && quiz && (
        <button
          onClick={handleSubmitQuiz}
          className="px-4 py-2 bg-green-500 rounded-md hover:bg-green-600 transition"
        >
          Submit
        </button>
      )}

      {/* Answer Sheet */}
      {isSubmitted && gradedResults && quiz && (
        <div className="mt-8 space-y-4">
          <h2 className="text-xl font-bold">Answer Sheet</h2>
          <p className="mb-4 font-semibold">
            Score: {gradedResults.tot_mark} / {quiz.questions.length}
          </p>
          {quiz.questions.map((q, i) => {
            const correct = gradedResults.marks[i] === 1;
            return (
              <div
                key={i}
                className={`p-4 rounded-md border-2 ${correct ? "border-green-500 bg-green-900/30" : "border-red-500 bg-red-900/30"}`}
              >
                <p className="font-semibold mb-1">Q{i + 1}: {q}</p>
                <p className={correct ? "text-green-400" : "text-red-400"}>
                  Your Answer: {userAnswers[i] || "Not answered"}
                </p>
                {!correct && <p className="text-green-300">Correct Answer: {quiz.answers[i]}</p>}
                <p className="text-gray-400 italic mt-1">Explanation: {quiz.explanations[i]}</p>
              </div>
            );
          })}

          <div className="pt-6 flex justify-center">
            <button
              onClick={() => {
                setQuiz(null);
                setGradedResults(null);
                setIsSubmitted(false);
                setUserAnswers([]);
                setSubject("");
                localStorage.removeItem("active_quiz");
                localStorage.removeItem("user_answers");
                localStorage.removeItem("graded_results");
                localStorage.removeItem("quiz_submitted");
              }}
              className="px-8 py-3 bg-theme-accent text-theme-bg font-bold rounded-md hover:bg-theme-accent-hover transition shadow-lg"
            >
              Finish Quiz and Return
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
