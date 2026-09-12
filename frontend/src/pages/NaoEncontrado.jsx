import { Emblema } from '../components/Emblema'
import { BotaoLink } from '../components/ui'

export function NaoEncontrado() {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-linear-to-br from-stone-100 via-emerald-50 to-amber-50 px-4">
      <Emblema className="pointer-events-none absolute -top-24 -right-24 h-112 w-md opacity-[0.06]" />

      <div className="relative flex flex-col items-center text-center animate-entrar">
        <Emblema className="h-20 w-20 opacity-60 grayscale" />
        <p className="mt-6 font-display text-6xl font-semibold text-emerald-950">404</p>
        <p className="mt-2 text-stone-500">Essa página não existe ou foi movida.</p>
        <BotaoLink to="/" variante="primario" className="mt-6">
          ← Voltar para o início
        </BotaoLink>
      </div>
    </div>
  )
}
