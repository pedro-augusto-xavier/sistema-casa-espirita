import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Modal } from './Modal'
import { SeletorPessoa } from './SeletorPessoa'

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
      <form onSubmit={aoEnviar} className="flex flex-col gap-4">
        <Campo label="Tipo de tratamento">
          <select
            value={tipoId}
            onChange={(e) => setTipoId(e.target.value)}
            className={estiloInput}
          >
            {tipos.map((t) => (
              <option key={t.id} value={t.id}>
                {t.nome}
              </option>
            ))}
          </select>
        </Campo>

        <Campo label="Solicitante / responsável (opcional)">
          <SeletorPessoa
            valor={solicitante}
            aoSelecionar={setSolicitante}
            placeholder="Buscar pessoa..."
          />
        </Campo>

        <Campo label="Número de sessões previstas (opcional)">
          <input
            type="number"
            min="0"
            value={sessoesPrevistas}
            onChange={(e) => setSessoesPrevistas(e.target.value)}
            className={estiloInput}
          />
        </Campo>

        <Campo label="Observação">
          <textarea
            rows={2}
            value={observacao}
            onChange={(e) => setObservacao(e.target.value)}
            className={estiloInput}
          />
        </Campo>

        {erro && (
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{erro}</p>
        )}

        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onFechar}
            className="rounded-md border border-stone-300 px-4 py-2 text-sm hover:bg-stone-50"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={enviando}
            className="rounded-md bg-emerald-800 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {enviando ? 'Salvando...' : 'Abrir caso'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

const estiloInput =
  'w-full rounded-md border border-stone-300 px-3 py-2 text-sm outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15'

function Campo({ label, children }) {
  return (
    <label className="block text-sm font-medium text-stone-700">
      {label}
      <div className="mt-1">{children}</div>
    </label>
  )
}
