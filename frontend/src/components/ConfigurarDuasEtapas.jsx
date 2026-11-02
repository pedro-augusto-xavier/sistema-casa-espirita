import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import { QrCode } from './QrCode'
import { Botao, Campo, Carregando, MensagemErro } from './ui'

/** Agrupa o segredo de 4 em 4 pra ficar fácil de digitar à mão. */
function emGrupos(segredo) {
  return segredo.match(/.{1,4}/g)?.join(' ') ?? segredo
}

/**
 * Liga a verificação em duas etapas: a pessoa escaneia o QR code com um
 * aplicativo autenticador (Google Authenticator, Microsoft Authenticator...)
 * e confirma digitando o primeiro código.
 */
export function ConfigurarDuasEtapas({ aoConcluir, aoCancelar }) {
  const [dados, setDados] = useState(null) // { segredo, uri }
  const [codigo, setCodigo] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)
  const iniciado = useRef(false)

  useEffect(() => {
    // em desenvolvimento o React roda efeitos 2x -- e cada chamada gera um
    // segredo novo; o ref garante uma só
    if (iniciado.current) return
    iniciado.current = true
    api
      .post('/auth/mfa/iniciar')
      .then(setDados)
      .catch((e) => setErro(e.message))
  }, [])

  async function confirmar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await api.post('/auth/mfa/ativar', { codigo })
      await aoConcluir()
    } catch (e) {
      setErro(e.message)
      setCodigo('')
    } finally {
      setEnviando(false)
    }
  }

  if (!dados) {
    return erro ? <MensagemErro>{erro}</MensagemErro> : <Carregando texto="Preparando..." />
  }

  return (
    <form onSubmit={confirmar} className="flex flex-col gap-4 text-sm text-stone-600">
      <ol className="ml-4 list-decimal space-y-1.5">
        <li>
          Instale no celular um aplicativo autenticador:{' '}
          <span className="font-medium text-stone-800">Google Authenticator</span> ou{' '}
          <span className="font-medium text-stone-800">Microsoft Authenticator</span> (são
          gratuitos).
        </li>
        <li>No aplicativo, toque em “+” / “Adicionar conta” e escaneie o QR code abaixo.</li>
        <li>Digite o código de 6 números que aparecer.</li>
      </ol>

      <div className="flex flex-col items-center gap-2 rounded-xl bg-stone-50 p-4 ring-1 ring-stone-900/5">
        <QrCode texto={dados.uri} />
        <details className="text-center text-xs text-stone-500">
          <summary className="cursor-pointer hover:text-emerald-800">
            Não consegue escanear? Digite esta chave no aplicativo
          </summary>
          <p className="mt-2 font-mono text-sm tracking-wider break-all text-stone-800 select-all">
            {emGrupos(dados.segredo)}
          </p>
        </details>
      </div>

      <Campo label="Código do aplicativo">
        <input
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={7}
          required
          value={codigo}
          onChange={(e) => setCodigo(e.target.value.replace(/[^\d ]/g, ''))}
          className="campo text-center font-mono text-xl tracking-[0.4em]"
        />
      </Campo>

      <MensagemErro>{erro}</MensagemErro>

      <div className="flex justify-end gap-2">
        {aoCancelar && (
          <Botao variante="secundario" type="button" onClick={aoCancelar}>
            Cancelar
          </Botao>
        )}
        <Botao type="submit" disabled={enviando || codigo.replace(/\D/g, '').length !== 6}>
          {enviando ? 'Conferindo...' : 'Ativar'}
        </Botao>
      </div>
    </form>
  )
}
