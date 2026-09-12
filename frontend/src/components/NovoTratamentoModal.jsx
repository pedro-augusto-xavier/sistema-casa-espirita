import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Modal } from './Modal'
import { SeletorPessoa } from './SeletorPessoa'
import { Botao, Campo, MensagemErro } from './ui'

export function NovoTratamentoModal({ pessoaId, onFechar, onCriado }) {
  const [tipos, setTipos] = useState([])
  const [tipoId, setTipoId] = useState('')
  const [solicitante, setSolicitante] = useState(null)
  const [sessoesPrevistas, setSessoesPrevistas] = useState('')
  const [observacao, setObservacao] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    api
      .get('/tipos-tratamento?formato=caso')
      .then((lista) => {
        setTipos(lista)
        if (lista.length > 0) setTipoId(String(lista[0].id))
      })
      .catch((e) => setErro(e.message))
  }, [])

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')

    if (!tipoId) {
      setErro('Escolha o tipo de tratamento.')
      return
    }

    setEnviando(true)
    try {
      await api.post('/tratamentos', {
        tipo_tratamento_id: Number(tipoId),
        solicitante_id: solicitante?.id ?? null,
        sessoes_previstas: sessoesPrevistas ? Number(sessoesPrevistas) : null,
        observacao: observacao || null,
        assistidos: [{ pessoa_id: pessoaId }],
      })
      onCriado()
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal titulo="Abrir tratamento" onFechar={onFechar}>
      <p className="-mt-2 mb-4 text-sm text-stone-500">
        Um tratamento é um caso que acompanha a pessoa por várias sessões, com diário de evolução.
      </p>
      <form onSubmit={aoEnviar} className="flex flex-col gap-4">
        <Campo label="Tipo de tratamento">
          <select value={tipoId} onChange={(e) => setTipoId(e.target.value)} className="campo">
            {tipos.map((t) => (
              <option key={t.id} value={t.id}>
                {t.nome}
              </option>
            ))}
          </select>
        </Campo>

        <Campo label="Solicitante / responsável" dica="opcional">
          <SeletorPessoa
            valor={solicitante}
            aoSelecionar={setSolicitante}
            placeholder="Buscar pessoa..."
          />
        </Campo>

        <Campo label="Sessões previstas" dica="opcional">
          <input
            type="number"
            min="0"
            value={sessoesPrevistas}
            onChange={(e) => setSessoesPrevistas(e.target.value)}
            className="campo w-32"
          />
        </Campo>

        <Campo label="Observação">
          <textarea
            rows={3}
            value={observacao}
            onChange={(e) => setObservacao(e.target.value)}
            className="campo"
          />
        </Campo>

        <MensagemErro>{erro}</MensagemErro>

        <div className="flex justify-end gap-2 pt-1">
          <Botao variante="secundario" onClick={onFechar}>
            Cancelar
          </Botao>
          <Botao type="submit" disabled={enviando}>
            {enviando ? 'Salvando...' : 'Abrir caso'}
          </Botao>
        </div>
      </form>
    </Modal>
  )
}
