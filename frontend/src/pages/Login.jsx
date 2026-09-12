import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { Emblema } from '../components/Emblema'
import { Botao, MensagemErro } from '../components/ui'

export function Login() {
  const { entrar } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await entrar(email, senha)
      navigate('/')
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-linear-to-br from-stone-100 via-emerald-50 to-amber-50 px-4 py-10">
      {/* marca d'água do brasão ao fundo */}
      <Emblema className="pointer-events-none absolute -top-24 -right-24 h-112 w-md opacity-[0.06]" />
      <Emblema className="pointer-events-none absolute -bottom-32 -left-32 h-96 w-96 opacity-[0.05]" />

      <div className="relative w-full max-w-sm animate-entrar">
        <div className="flex flex-col items-center text-center">
          <Emblema className="h-24 w-24 drop-shadow-sm" />
          <h1 className="mt-5 font-display text-3xl font-semibold tracking-wide text-emerald-950">
            Casa Espírita
            <br />
            Amor e Perdão
          </h1>
          <p className="mt-2 text-xs font-medium tracking-[0.25em] text-stone-500 uppercase">
            Nova Friburgo · RJ
          </p>
        </div>

        <form
          onSubmit={aoEnviar}
          className="mt-8 w-full rounded-2xl border border-white/70 bg-white/85 p-8 shadow-xl shadow-emerald-900/10 ring-1 ring-stone-900/5 backdrop-blur-sm"
        >
          <p className="text-sm text-stone-500">Entre com seu e-mail e senha.</p>

          <label className="mt-6 block text-sm font-medium text-stone-700">
            E-mail
            <input
              type="email"
              required
              autoFocus
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="campo mt-1"
            />
          </label>

          <label className="mt-4 block text-sm font-medium text-stone-700">
            Senha
            <input
              type="password"
              required
              autoComplete="current-password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              className="campo mt-1"
            />
          </label>

          <MensagemErro className="mt-4">{erro}</MensagemErro>

          <Botao type="submit" disabled={enviando} className="mt-6 w-full">
            {enviando ? 'Entrando...' : 'Entrar'}
          </Botao>
        </form>

        <p className="mt-6 text-center text-xs text-stone-400">
          Acesso restrito à equipe da casa.
        </p>
      </div>
    </div>
  )
}
