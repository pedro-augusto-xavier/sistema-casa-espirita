import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { Emblema } from './Emblema'

export function Cabecalho() {
  const { usuario, sair } = useAuth()

  return (
    <header className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3 bg-white px-4 py-3 shadow-sm ring-1 ring-stone-900/5 sm:px-6 sm:py-4">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
        <Link to="/" className="flex items-center gap-2.5">
          <Emblema className="h-9 w-9 shrink-0" />
          <span className="flex flex-col leading-tight">
            <span className="font-display text-base font-semibold text-emerald-900 sm:text-lg">
              Casa Espírita Amor e Perdão
            </span>
            <span className="text-[10px] font-medium uppercase tracking-widest text-stone-400">
              Nova Friburgo - RJ
            </span>
          </span>
        </Link>
        <nav className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <Link to="/grupos" className="text-sm text-stone-500 hover:text-emerald-800">
            Grupos
          </Link>
          <Link to="/agenda" className="text-sm text-stone-500 hover:text-emerald-800">
            Agenda
          </Link>
          {usuario.papel === 'admin' && (
            <>
              <Link to="/usuarios" className="text-sm text-stone-500 hover:text-emerald-800">
                Usuários
              </Link>
              <Link to="/auditoria" className="text-sm text-stone-500 hover:text-emerald-800">
                Auditoria
              </Link>
            </>
          )}
        </nav>
      </div>
      <div className="flex items-center gap-4 text-sm text-stone-600">
        <span>
          {usuario.nome} <span className="text-stone-400">({usuario.papel})</span>
        </span>
        <button
          onClick={sair}
          className="rounded-md border border-stone-300 px-3 py-1 hover:bg-stone-50"
        >
          Sair
        </button>
      </div>
    </header>
  )
}
