export type LoginResponse = {
  user_id: number
  username: string
  course_id?: string
  education_level?: string
}

export type FileItem = { id: number; file_name: string; file_type: string; uploaded_at: string }

export type AnalysisResponse = { analysis: string; timetable: string; roadmap: string; timestamp: string }


