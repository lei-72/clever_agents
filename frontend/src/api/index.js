import request from '@/utils/request'
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const authApi = {
  login: (data) => request.post('/auth/login', data),
  register: (data) => request.post('/auth/register', data),
  getMe: () => request.get('/rbac/me'),
}

export const systemApi = {
  health: () => request.get('/system/health'),
  ready: () => request.get('/system/ready'),
  llm: () => request.get('/system/llm'),
}

export const qaApi = {
  ask: (data) => request.post('/qa/ask', data),
  askStream: async (data, handlers = {}) => {
    const token = localStorage.getItem('token')
    const response = await fetch(`${apiBaseUrl}/qa/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
    })
    if (!response.ok || !response.body) {
      throw new Error(`stream request failed: ${response.status}`)
    }

    const decoder = new TextDecoder()
    const reader = response.body.getReader()
    let buffer = ''

    const dispatch = (rawEvent) => {
      const lines = rawEvent.split('\n')
      const eventLine = lines.find((line) => line.startsWith('event:'))
      const dataLine = lines.filter((line) => line.startsWith('data:')).map((line) => line.slice(5).trim()).join('\n')
      if (!dataLine) return
      let payload
      try {
        payload = JSON.parse(dataLine)
      } catch {
        return
      }
      const evt = payload.event || (eventLine ? eventLine.replace('event:', '').trim() : '')
      const dataPayload = payload.data || payload
      if (evt === 'delta' && handlers.onDelta) handlers.onDelta(dataPayload.content || '')
      if (evt === 'meta' && handlers.onMeta) handlers.onMeta(dataPayload)
      if (evt === 'progress' && handlers.onProgress) handlers.onProgress(dataPayload.message || '')
      if (evt === 'error' && handlers.onError) handlers.onError(dataPayload.message || '流式请求失败')
      if (evt === 'done' && handlers.onDone) handlers.onDone(dataPayload)
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split('\n\n')
      buffer = events.pop() || ''
      events.forEach(dispatch)
    }
  },
  ingest: (data) => request.post('/qa/ingest', data),
  ingestFile: (formData) =>
    request.post('/qa/ingest-file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

export const gradingApi = {
  grade: (data) => request.post('/grading/grade', data),
  reviewPublish: (data) => request.post('/grading/review-publish', data),
}

export const resumeApi = {
  review: (data) => request.post('/resume/review', data),
}

export const interviewApi = {
  start: (data) => request.post('/interview/start', data),
  answer: (sessionId, data) => request.post(`/interview/${sessionId}/answer`, data),
  getSession: (sessionId) => request.get(`/interview/${sessionId}`),
  generateReport: (sessionId) => request.post(`/interview/${sessionId}/report/generate`),
  getReport: (sessionId) => request.get(`/interview/${sessionId}/report`),
}

export const orchestratorApi = {
  route: (data) => request.post('/orchestrator/route', data),
  execute: (data) => request.post('/orchestrator/execute', data),
}
