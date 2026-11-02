import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { Emblema } from '../components/Emblema'
import { Botao, MensagemErro } from '../components/ui'

export function Login() {
  const { entrar } = useAuth()
  const navigate = useNavigate()

  const nomeSalvo = localStorage.getItem('ultimoNome') ?? ''
  const [nome, setNome] = useState(nomeSalvo)
  const [senha, setSenha] = useState('')
  const [lembrar, setLembrar] = useState(true)
  // 2ª etapa: o código de 6 números do aplicativo autenticador
  const [pedindoCodigo, setPedindoCodigo] = useState(false)
  const [codigo, setCodigo] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await entrar(nome, senha, lembrar, pedindoCodigo ? codigo : '')
      navigate('/')
    } catch (e) {
      if (e.codigo === 'mfa_necessario') {
        setPedindoCodigo(true)
      } else {
        setErro(e.message)
        if (e.codigo === 'mfa_invalido') setCodigo('')
      }
    } finally {
      setEnviando(false)
    }
  }

  function voltar() {
    setPedindoCodigo(false)
    setCodigo('')
    setSenha('')
    setErro('')
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
          method="post"
          onSubmit={aoEnviar}
          className="mt-8 w-full rounded-2xl border border-white/70 bg-white/85 p-8 shadow-xl shadow-emerald-900/10 ring-1 ring-stone-900/5 backdrop-blur-sm"
        >
          {pedindoCodigo ? (
            <>
              <p className="text-sm text-stone-600">
                Abra o aplicativo autenticador no celular e digite o código de 6 números de{' '}
                <span className="font-medium text-stone-800">Casa Espírita Amor e Perdão</span>.
              </p>

              <label className="mt-6 block text-sm font-medium text-stone-700">
                Código
                <input
                  type="text"
                  name="codigo"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="[0-9 ]{6,7}"
                  maxLength={7}
                  required
                  autoFocus
                  value={codigo}
                  onChange={(e) => setCodigo(e.target.value.replace(/[^\d ]/g, ''))}
                  className="campo mt-1 text-center font-mono text-2xl tracking-[0.4em]"
                />
              </label>

              <MensagemErro className="mt-4">{erro}</MensagemErro>

              <Botao type="submit" disabled={enviando} className="mt-6 w-full">
                {enviando ? 'Conferindo...' : 'Entrar'}
              </Botao>
              <button
                type="button"
                onClick={voltar}
                className="mt-3 w-full text-center text-xs text-stone-500 hover:text-emerald-800 hover:underline"
              >
                ← Voltar
              </button>
            </>
          ) : (
            <>
              <p className="text-sm text-stone-500">Entre com seu nome e senha.</p>

              <label className="mt-6 block text-sm font-medium text-stone-700">
                Nome
                <input
                  type="text"
                  name="username"
                  required
                  autoFocus={!nomeSalvo}
                  autoComplete="username"
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  className="campo mt-1"
                />
              </label>

              <label className="mt-4 block text-sm font-medium text-stone-700">
                Senha
                <input
                  type="password"
                  name="password"
                  required
                  autoFocus={!!nomeSalvo}
                  autoComplete="current-password"
                  value={senha}
                  onChange={(e) => setSenha(e.target.value)}
                  className="campo mt-1"
                />
              </label>

              <label className="mt-4 flex items-center gap-2 text-sm text-stone-600">
                <input
                  type="checkbox"
                  checked={lembrar}
                  onChange={(e) => setLembrar(e.target.checked)}
                  className="h-4 w-4 rounded border-stone-300 accent-emerald-700"
                />
                Manter conectado neste aparelho
              </label>

              <MensagemErro className="mt-4">{erro}</MensagemErro>

              <Botao type="submit" disabled={enviando} className="mt-6 w-full">
                {enviando ? 'Entrando...' : 'Entrar'}
              </Botao>
            </>
          )}
        </form>

        <p className="mt-6 text-center text-xs text-stone-400">
          Acesso restrito à equipe da casa ·{' '}
          <Link to="/privacidade" className="underline hover:text-emerald-800">
            Privacidade
          </Link>
        </p>
      </div>
    </div>
  )
}
