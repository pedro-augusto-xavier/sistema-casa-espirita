import { useState } from 'react'
import { api } from '../api/client'
import { Modal } from './Modal'
import { Botao, Campo, MensagemErro } from './ui'

/**
 * Pra quem entrou com uma senha provisória (ex: o CPF, gerado no cadastro
 * rápido) trocar por uma só sua -- sem precisar pedir pra um admin.
 */
export function TrocarSenhaModal({ onFechar }) {
  const [senhaAtual, setSenhaAtual] = useState('')
  const [senhaNova, setSenhaNova] = useState('')
  const [confirmacao, setConfirmacao] = useState('')
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState(false)
  const [enviando, setEnviando] = useState(false)

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')

    if (senhaNova.length < 8) {
      setErro('A senha nova precisa ter pelo menos 8 caracteres.')
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
      setSucesso(true)
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  if (sucesso) {
    return (
      <Modal titulo="Senha trocada" onFechar={onFechar}>
        <p className="text-sm text-stone-600">
          Pronto — da próxima vez, entre com a senha nova.
        </p>
        <div className="mt-5 flex justify-end">
          <Botao onClick={onFechar}>Fechar</Botao>
        </div>
      </Modal>
    )
  }

  return (
    <Modal titulo="Trocar minha senha" onFechar={onFechar}>
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

        <Campo label="Senha nova" dica="8+ caracteres">
          <input
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={senhaNova}
            onChange={(e) => setSenhaNova(e.target.value)}
            className="campo"
          />
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
          <Botao variante="secundario" type="button" onClick={onFechar}>
            Cancelar
          </Botao>
          <Botao type="submit" disabled={enviando}>
            {enviando ? 'Salvando...' : 'Trocar senha'}
          </Botao>
        </div>
      </form>
    </Modal>
  )
}
