// Cliente simples de API: monta a URL, manda o token e trata erro padrão.

const BASE_URL = import.meta.env.VITE_API_URL

function pegarToken() {
  return localStorage.getItem('token')
}

async function request(path, { method = 'GET', body, isForm = false } = {}) {
  const headers = {}
  const token = pegarToken()
  if (token) headers.Authorization = `Bearer ${token}`
  if (body && !isForm) headers['Content-Type'] = 'application/json'

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
  })

  // 401 na própria tentativa de login é "senha errada", não "sessão expirada"
  // -- deixa cair pro tratamento padrão, que mostra a mensagem real da API.
  if (res.status === 401 && path !== '/auth/login') {
    localStorage.removeItem('token')
    if (location.pathname !== '/login') location.href = '/login'
    throw new Error('Sessão expirada, faça login de novo.')
  }

  if (!res.ok) {
    const corpo = await res.json().catch(() => null)
    const mensagem = extrairMensagemDeErro(corpo)
    throw new Error(mensagem)
  }

  if (res.status === 204) return null
  return res.json()
}

function extrairMensagemDeErro(corpo) {
  if (!corpo?.detail) return 'Erro inesperado na API.'
  if (typeof corpo.detail === 'string') return corpo.detail
  // erro de validação do Pydantic: lista de {loc, msg}
  if (Array.isArray(corpo.detail)) {
    return corpo.detail.map((e) => `${e.loc?.at(-1)}: ${e.msg}`).join(' | ')
  }
  return JSON.stringify(corpo.detail)
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body }),
  patch: (path, body) => request(path, { method: 'PATCH', body }),
  del: (path) => request(path, { method: 'DELETE' }),

  login: (email, senha) => {
    const form = new URLSearchParams({ username: email, password: senha })
    return request('/auth/login', { method: 'POST', body: form, isForm: true })
  },
}
