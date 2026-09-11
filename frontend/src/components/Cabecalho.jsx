import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export function Cabecalho() {
  const { usuario, sair } = useAuth()

  return (
    <header className="flex items-center justify-between bg-white px-6 py-4 shadow-sm">
      <div className="flex items-center gap-6">
        <Link to="/" className="text-lg font-bold text-slate-800">
          Casa Espírita
        </Link>
        {usuario.papel === 'admin' && (
          <Link to="/usuarios" className="text-sm text-slate-500 hover:text-slate-800">
            Usuários
          </Link>
        )}
      </div>
      <div className="flex items-center gap-4 text-sm text-slate-600">
        <span>
          {usuario.nome} <span className="text-slate-400">({usuario.papel})</span>
        </span>
        <button
          onClick={sair}
          className="rounded-md border border-slate-300 px-3 py-1 hover:bg-slate-50"
        >
          Sair
        </button>
      </div>
    </header>
  )
}
