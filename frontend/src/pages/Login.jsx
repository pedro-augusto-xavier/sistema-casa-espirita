import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { Emblema } from '../components/Emblema'

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
    <div className="flex min-h-screen items-center justify-center bg-linear-to-br from-stone-100 via-emerald-50 to-amber-50 px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center text-center">
          <Emblema className="h-20 w-20" />
          <h1 className="mt-4 font-display text-2xl font-semibold tracking-wide text-emerald-900">
            Casa Espírita Amor e Perdão
          </h1>
          <p className="mt-1 text-xs font-medium uppercase tracking-widest text-stone-500">
            Nova Friburgo — RJ
          </p>
        </div>

        <form
          onSubmit={aoEnviar}
          className="mt-8 w-full rounded-xl border border-stone-200/70 bg-white/90 p-8 shadow-xl shadow-stone-900/5 ring-1 ring-stone-900/5 backdrop-blur-sm"
        >
          <p className="text-sm text-stone-500">Entre com seu e-mail e senha.</p>

          <label className="mt-6 block text-sm font-medium text-stone-700">
            E-mail
            <input
              type="email"
              required
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-md border border-stone-300 px-3 py-2 text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15"
            />
          </label>

          <label className="mt-4 block text-sm font-medium text-stone-700">
            Senha
            <input
              type="password"
              required
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              className="mt-1 w-full rounded-md border border-stone-300 px-3 py-2 text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15"
            />
          </label>

          {erro && (
            <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {erro}
            </p>
          )}

          <button
            type="submit"
            disabled={enviando}
            className="mt-6 w-full rounded-md bg-emerald-800 py-2 text-sm font-medium text-white shadow-sm hover:bg-emerald-700 disabled:opacity-50"
          >
            {enviando ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}
