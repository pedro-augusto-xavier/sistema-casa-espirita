import { Navigate } from 'react-router-dom'
import { Emblema } from '../components/Emblema'
import { BotaoLink } from '../components/ui'
import { PrimeiroAcesso } from '../pages/PrimeiroAcesso'
import { useAuth } from './AuthContext'

/** Só deixa passar se tiver usuário logado e sem pendência; senão manda pro
 * /login (ou mostra a tela de primeiro acesso). */
export function RotaProtegida({ children, somenteAdmin = false }) {
  const { usuario, carregando } = useAuth()

  if (carregando) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-stone-100">
        <Emblema className="h-16 w-16 animate-pulse opacity-70" />
        <p className="text-sm text-stone-400">Abrindo o sistema...</p>
      </div>
    )
  }

  if (!usuario) return <Navigate to="/login" replace />

  // senha provisória pra trocar / código do celular pra configurar
  if (usuario.pendencias?.length) return <PrimeiroAcesso />

  if (somenteAdmin && usuario.papel !== 'admin') {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-stone-100 px-4 text-center">
        <Emblema className="h-16 w-16 opacity-40 grayscale" />
        <p className="mt-5 font-display text-2xl font-semibold text-emerald-950">
          Área restrita
        </p>
        <p className="mt-1 max-w-sm text-sm text-stone-500">
          Só administradores podem ver esta página. Fale com quem cuida do sistema se precisar
          de acesso.
        </p>
        <BotaoLink to="/" variante="primario" className="mt-6">
          ← Voltar para o início
        </BotaoLink>
      </div>
    )
  }

  return children
}
