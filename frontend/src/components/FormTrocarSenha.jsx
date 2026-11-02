import { useState } from 'react'
import { api } from '../api/client'
import { dicasDaSenha, senhaPassaNasDicas } from '../utils/senha'
import { Botao, Campo, MensagemErro } from './ui'

/**
 * Trocar a própria senha. Usado no primeiro acesso (senha provisória, ex: o
 * CPF) e no "Minha conta". As regras de verdade ficam na API: aqui só
 * mostramos as dicas enquanto a pessoa digita.
 */
export function FormTrocarSenha({ aoConcluir, aoCancelar, textoBotao = 'Trocar senha' }) {
  const [senhaAtual, setSenhaAtual] = useState('')
  const [senhaNova, setSenhaNova] = useState('')
  const [confirmacao, setConfirmacao] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')

    if (!senhaPassaNasDicas(senhaNova)) {
      setErro('A senha nova ainda não segue as dicas abaixo do campo.')
      return
    }
    if (senhaNova !== confirmacao) {
      setErro('A confirmação não bate com a senha nova.')
      return
    }

    setEnviando(true)
    try {
      await api.post('/auth/trocar-senha', {
        senha_atual: senhaAtual,
        senha_nova: senhaNova,
      })
      await aoConcluir()
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={aoEnviar} className="flex flex-col gap-4">
      <Campo label="Senha atual">
        <input
          type="password"
          required
          autoFocus
          autoComplete="current-password"
          value={senhaAtual}
          onChange={(e) => setSenhaAtual(e.target.value)}
          className="campo"
        />
      </Campo>

      <Campo label="Senha nova">
        <input
          type="password"
          required
          autoComplete="new-password"
          value={senhaNova}
          onChange={(e) => setSenhaNova(e.target.value)}
          className="campo"
        />
        <ul className="mt-2 flex flex-col gap-1 text-xs">
          {dicasDaSenha(senhaNova).map((d) => (
            <li key={d.texto} className={d.ok ? 'text-emerald-700' : 'text-stone-400'}>
              {d.ok ? '✓' : '○'} {d.texto}
            </li>
          ))}
          <li className="text-stone-400">
            ○ Nada de nome, CPF, data de nascimento ou o nome da casa
          </li>
        </ul>
        <p className="mt-2 text-xs text-stone-500">
          Dica: uma frase curta é fácil de lembrar e difícil de adivinhar — ex.{' '}
          <span className="font-medium">girassol amarelo na janela</span>.
        </p>
      </Campo>

      <Campo label="Confirmar a senha nova">
        <input
          type="password"
          required
          autoComplete="new-password"
          value={confirmacao}
          onChange={(e) => setConfirmacao(e.target.value)}
          className="campo"
        />
      </Campo>

      <MensagemErro>{erro}</MensagemErro>

      <div className="flex justify-end gap-2 pt-1">
        {aoCancelar && (
          <Botao variante="secundario" type="button" onClick={aoCancelar}>
            Cancelar
          </Botao>
        )}
        <Botao type="submit" disabled={enviando}>
          {enviando ? 'Salvando...' : textoBotao}
        </Botao>
      </div>
    </form>
  )
}
