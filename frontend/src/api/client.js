// Cliente simples de API: monta a URL, manda o token e trata erro padrão.
//
// O token fica no localStorage. Ele sozinho não basta: o servidor confere a
// sessão a cada chamada, então "Sair" (ou o admin desativar alguém) corta o
// acesso na hora. E o site roda com uma CSP rígida (vercel.json), que barra
// script de fora -- a forma comum de roubar token guardado no navegador.

const BASE_URL = import.meta.env.VITE_API_URL

/** Erro da API com o status e, quando houver, um código que a tela entende
 * (ex: "mfa_necessario" no login, "pendencia" quando falta trocar a senha). */
export class ErroApi extends Error {
  constructor(mensagem, { status, codigo = null, detalhe = null } = {}) {
    super(mensagem)
    this.status = status
    this.codigo = codigo
    this.detalhe = detalhe
  }
}

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
    throw new ErroApi('Sessão encerrada, entre de novo.', { status: 401 })
  }

  if (!res.ok) {
    const corpo = await res.json().catch(() => null)
    const erro = criarErro(res.status, corpo)
    // ainda falta trocar a senha / configurar o código: a tela de acesso
    // cuida disso (ver AuthContext)
    if (erro.codigo === 'pendencia') window.dispatchEvent(new Event('acesso-pendente'))
    throw erro
  }

  if (res.status === 204) return null
  return res.json()
}

/** Baixa um arquivo (anexo) autenticado, como Blob -- pra exibir com
 * <img>/abrir num link, já que a rota exige o token do localStorage. */
async function requestBlob(path) {
  const headers = {}
  const token = pegarToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${BASE_URL}${path}`, { headers })
  if (!res.ok) throw new ErroApi('Não foi possível baixar o arquivo.', { status: res.status })
  return res.blob()
}

function criarErro(status, corpo) {
  const detalhe = corpo?.detail
  if (!detalhe) return new ErroApi('Erro inesperado na API.', { status })
  if (typeof detalhe === 'string') return new ErroApi(detalhe, { status })
  // erro de validação do Pydantic: lista de {loc, msg}
  if (Array.isArray(detalhe)) {
    const mensagem = detalhe.map((e) => `${e.loc?.at(-1)}: ${e.msg}`).join(' | ')
    return new ErroApi(mensagem, { status })
  }
  // erro com código: {codigo, mensagem}
  if (detalhe.mensagem) {
    return new ErroApi(detalhe.mensagem, { status, codigo: detalhe.codigo, detalhe })
  }
  return new ErroApi(JSON.stringify(detalhe), { status })
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body }),
  postForm: (path, formData) => request(path, { method: 'POST', body: formData, isForm: true }),
  patch: (path, body) => request(path, { method: 'PATCH', body }),
  del: (path) => request(path, { method: 'DELETE' }),
  getBlob: (path) => requestBlob(path),

  login: (nome, senha, lembrar = false, codigo = '') => {
    const form = new URLSearchParams({
      username: nome,
      password: senha,
      lembrar: String(lembrar),
    })
    if (codigo) form.set('codigo', codigo)
    return request('/auth/login', { method: 'POST', body: form, isForm: true })
  },

  /** Avisa a API que um PDF com dados da pessoa foi gerado (fica na
   * auditoria). Não trava o download se falhar. */
  registrarExportacao: (pessoaId, documento) =>
    request(`/pessoas/${pessoaId}/exportacoes`, {
      method: 'POST',
      body: { documento },
    }).catch(() => null),
}
