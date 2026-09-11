import { Link } from 'react-router-dom'

export function NaoEncontrado() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100">
      <div className="text-center">
        <p className="text-4xl font-bold text-slate-800">404</p>
        <p className="mt-2 text-slate-500">Essa página não existe.</p>
        <Link to="/" className="mt-4 inline-block text-sm text-slate-600 hover:underline">
          ← Voltar para o início
        </Link>
      </div>
    </div>
  )
}
