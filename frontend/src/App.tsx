import { Route, Routes, Navigate } from "react-router-dom";
import Login from "@/pages/Login";
import Signup from "@/pages/Signup";
import Dashboard from "@/pages/Dashboard";
import Syllabus from "@/pages/Syllabus";
import Recommendations from "@/pages/Recommendations";
import Quiz from "@/pages/Quiz";
import Chat from "@/pages/Chat";
import Files from "@/pages/Files";
import Performance from "@/pages/Performance";
import Admin from "@/pages/admin/Admin";
import AdminLogin from "@/pages/admin/AdminLogin";
import AppLayout from "@/components/AppLayout";



export default function App() {
  return (
    <div>


      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/app" element={<AppLayout />}>
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="syllabus" element={<Syllabus />} />
          <Route path="recommendations" element={<Recommendations />} />
          <Route path="quiz" element={<Quiz />} />
          <Route path="chat" element={<Chat />} />
          <Route path="files" element={<Files />} />
          <Route path="performance" element={<Performance />} />
        </Route>
        <Route path="/admin" element={<Admin />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </div>

  );
}
