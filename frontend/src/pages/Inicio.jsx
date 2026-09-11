import { useAuth } from '../auth/AuthContext'

export function Inicio() {
  const { usuario, sair } = useAuth()

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="flex items-center justify-between bg-white px-6 py-4 shadow-sm">
        <h1 className="text-lg font-bold text-slate-800">Casa Espírita</h1>
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

      <main className="p-6">
        <p className="text-slate-600">
          Login funcionando. A lista de pessoas entra aqui na próxima etapa.
        </p>
      </main>
    </div>
  )
}
