import { api } from './client'

export const Auth = {
  login: (username: string, password: string, admin_code: string) =>
    api.post('/auth/login', { username, password, admin_code }).then(r => r.data),
  changePassword: (user_id: number, new_password: string) =>
    api.post('/auth/change-password', { user_id, new_password }).then(r => r.data),
}

export const Admin = {
  check: () => api.get('/admin/auth/check').then(r => r.data),
  generateOtp: (email: string) => api.post('/admin/auth/generate-otp', { email }).then(r => r.data),
  setup: (payload: any) => api.post('/admin/auth/setup', payload).then(r => r.data),
  login: (payload: any) => api.post('/admin/auth/login', payload).then(r => r.data),
  signup: (payload: any) => api.post('/admin/auth/signup-student', payload).then(r => r.data),
  createUser: (payload: { username: string; password: string; course_id: string; education_level: string, admin_id: number }) =>
    api.post('/admin/users', payload).then(r => r.data),
  listUsers: () => api.get('/admin/users').then(r => r.data),
  listCourses: () => api.get('/admin/courses').then(r => r.data),
  usersByCourse: (course_id: string) => api.get(`/admin/courses/${course_id}/users`).then(r => r.data),
  groupsForUser: (user_id: number) => api.get(`/admin/users/${user_id}/groups`).then(r => r.data),
  createGroup: (user_id: number, group_name: string) => api.post(`/admin/users/${user_id}/groups`, { group_name }).then(r => r.data),
  uploadToGroup: (group_id: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/admin/groups/${group_id}/files`, form).then(r => r.data)
  },
  listFiles: (group_id: number) => api.get(`/admin/groups/${group_id}/files`).then(r => r.data),
  deleteFile: (file_id: number) => api.delete(`/admin/files/${file_id}`).then(r => r.data),
  getCourseSyllabus: (course_id: string) => api.get(`/admin/courses/${course_id}/syllabus`).then(r => r.data),
  saveCourseSyllabus: (course_id: string, syllabus_content: string) => api.put(`/admin/courses/${course_id}/syllabus`, { syllabus_content }).then(r => r.data),
}

export const Groups = {
  list: (user_id: number) => api.get(`/users/${user_id}/groups`).then(r => r.data),
  create: (user_id: number, group_name: string) => api.post(`/users/${user_id}/groups`, { group_name }).then(r => r.data),
}

export const Files = {
  upload: (group_id: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/groups/${group_id}/files`, form).then(r => r.data)
  },
  list: (group_id: number) => api.get(`/groups/${group_id}/files`).then(r => r.data),
  delete: (file_id: number) => api.delete(`/files/${file_id}`).then(r => r.data),
}

export const Syllabus = {
  getCourse: (course_id: string) => api.get(`/courses/${course_id}/syllabus`).then(r => r.data),
  getGroup: (group_id: number) => api.get(`/groups/${group_id}/syllabus`).then(r => r.data),
  saveGroup: (group_id: number, syllabus_content: string, ratings: Record<string, number>) =>
    api.put(`/groups/${group_id}/syllabus`, { syllabus_content, ratings }).then(r => r.data),
}

export const Analysis = {
  run: (group_id: number) => api.post(`/groups/${group_id}/analysis`).then(r => r.data),
  getLatest: (group_id: number) => api.get(`/groups/${group_id}/analysis`).then(r => r.data),

  // ADD THIS FUNCTION
  getStatus: (group_id: number) => api.get(`/groups/${group_id}/status`).then(r => r.data),
};


export const Recs = {
  youtube: (q: string) => api.get(`/recommendations/youtube?q=${encodeURIComponent(q)}`).then(r => r.data),
  web: (q: string) => api.get(`/recommendations/web?q=${encodeURIComponent(q)}`).then(r => r.data),
}

export const Quiz = {
  generate: (group_id: number, subject: string) => api.post(`/quizzes/groups/${group_id}/generate`, { subject }).then(r => r.data),
  grade: (correct_answers: string[], user_answers: string[]) => api.post('/quizzes/grade', { correct_answers, user_answers }).then(r => r.data),
  save: (
    group_id: number,
    user_id: number,
    body: {
      subject: string
      questions: string[]
      options: string[][]
      correct_answers: string[]
      user_answers: string[]
      marks: number[]
      explanations: string[]
      related_content: string[]
      related_videos: string[]
    }
  ) => api.post(`/quizzes/groups/${group_id}/save?user_id=${user_id}`, body).then(r => r.data),
  list: (group_id: number, user_id: number) => api.get(`/quizzes/groups/${group_id}?user_id=${user_id}`).then(r => r.data),
}

export const Chat = {
  listSessions: (user_id: number, group_id: number) =>
    api.get(`/chat/sessions?user_id=${user_id}&group_id=${group_id}`).then(r => r.data),
  text: (group_id: number, user_id: number, message: string, session_id: string) =>
    api.post(`/chat/groups/${group_id}/text`, { user_id, message, session_id }).then(r => r.data),
  textHistory: (group_id: number, user_id: number, session_id?: string) =>
    api.get(`/chat/groups/${group_id}/text?user_id=${user_id}${session_id ? `&session_id=${session_id}` : ''}`).then(r => r.data),
  image: (group_id: number, user_id: number, message: string, session_id: string, file?: File, image_url?: string) => {
    const form = new FormData()
    form.append('user_id', String(user_id))
    form.append('message', message)
    form.append('session_id', session_id)
    if (file) form.append('image', file)
    if (image_url) form.append('image_url', image_url)
    return api.post(`/chat/groups/${group_id}/image`, form).then(r => r.data)
  },
  imageHistory: (group_id: number, image_id: string, user_id: number, session_id?: string) =>
    api.get(`/chat/groups/${group_id}/image/${encodeURIComponent(image_id)}?user_id=${user_id}${session_id ? `&session_id=${session_id}` : ''}`).then(r => r.data),
  video: (group_id: number, user_id: number, message: string, session_id: string, video_url: string) =>
    api.post(`/chat/groups/${group_id}/video`, { user_id, message, session_id, video_url }).then(r => r.data),
  videoHistory: (group_id: number, video_id: string, user_id: number, session_id?: string) =>
    api.get(`/chat/groups/${group_id}/video/${encodeURIComponent(video_id)}?user_id=${user_id}${session_id ? `&session_id=${session_id}` : ''}`).then(r => r.data),
}

export const Performance = {
  list: (group_id: number, user_id: number) => api.get(`/groups/${group_id}/performance?user_id=${user_id}`).then(r => r.data),
}


