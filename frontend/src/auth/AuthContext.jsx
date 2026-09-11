import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      setCarregando(false)
      return
    }
    api
      .get('/auth/me')
      .then(setUsuario)
      .catch(() => localStorage.removeItem('token'))
      .finally(() => setCarregando(false))
  }, [])

  async function entrar(email, senha) {
    const { access_token } = await api.login(email, senha)
    localStorage.setItem('token', access_token)
    const eu = await api.get('/auth/me')
    setUsuario(eu)
  }

  function sair() {
    localStorage.removeItem('token')
    setUsuario(null)
  }

  return (
    <AuthContext.Provider value={{ usuario, carregando, entrar, sair }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const contexto = useContext(AuthContext)
  if (!contexto) throw new Error('useAuth precisa estar dentro de <AuthProvider>')
  return contexto
}
