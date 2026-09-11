import { Navigate } from 'react-router-dom'
import { useAuth } from './AuthContext'

/** Só deixa passar se tiver usuário logado; senão manda pro /login. */
export function RotaProtegida({ children, somenteAdmin = false }) {
  const { usuario, carregando } = useAuth()

  if (carregando) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-500">
        Carregando...
      </div>
    )
  }

  if (!usuario) return <Navigate to="/login" replace />

  if (somenteAdmin && usuario.papel !== 'admin') {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-500">
        Você não tem permissão para ver esta página.
      </div>
    )
  }

  return children
}
