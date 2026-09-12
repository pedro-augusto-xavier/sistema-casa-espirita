import { Link } from 'react-router-dom'

export function NaoEncontrado() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-linear-to-br from-stone-100 via-emerald-50 to-amber-50">
      <div className="text-center">
        <p className="font-display text-5xl font-semibold text-emerald-900">404</p>
        <p className="mt-2 text-stone-500">Essa página não existe.</p>
        <Link
          to="/"
          className="mt-4 inline-block text-sm text-emerald-800 hover:underline"
        >
          ← Voltar para o início
        </Link>
      </div>
    </div>
  )
}
