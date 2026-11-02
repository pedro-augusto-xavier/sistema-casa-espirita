import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [carregando, setCarregando] = useState(true)

  const recarregar = useCallback(async () => {
    const eu = await api.get('/auth/me')
    setUsuario(eu)
    return eu
  }, [])

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      setCarregando(false)
      return
    }
    recarregar()
      .catch(() => localStorage.removeItem('token'))
      .finally(() => setCarregando(false))
  }, [recarregar])

  // a API avisou que falta algo (ex: o admin pediu pra trocar a senha, ou
  // virou admin e agora precisa do código): recarrega e a tela de acesso
  // aparece sozinha
  useEffect(() => {
    function aoPendente() {
      recarregar().catch(() => {})
    }
    window.addEventListener('acesso-pendente', aoPendente)
    return () => window.removeEventListener('acesso-pendente', aoPendente)
  }, [recarregar])

  /** Lança ErroApi com codigo "mfa_necessario" quando falta o código do
   * aplicativo -- a tela de login pede e chama de novo com `codigo`. */
  async function entrar(nome, senha, lembrar = false, codigo = '') {
    const { access_token } = await api.login(nome, senha, lembrar, codigo)
    localStorage.setItem('token', access_token)
    // guarda o nome pra já vir preenchido na próxima vez (nunca a senha --
    // essa fica a cargo do gerenciador de senhas do navegador)
    if (lembrar) localStorage.setItem('ultimoNome', nome.trim())
    else localStorage.removeItem('ultimoNome')
    await recarregar()
  }

  async function sair() {
    // encerra a sessão no servidor: o token deixa de valer na hora, mesmo
    // que alguém tenha copiado
    try {
      await api.post('/auth/logout')
    } catch {
      // sessão já tinha caído -- tudo bem
    }
    localStorage.removeItem('token')
    setUsuario(null)
  }

  return (
    <AuthContext.Provider value={{ usuario, carregando, entrar, sair, recarregar }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const contexto = useContext(AuthContext)
  if (!contexto) throw new Error('useAuth precisa estar dentro de <AuthProvider>')
  return contexto
}
