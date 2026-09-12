import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { dataParaIso, isoParaData, mascaraData } from '../utils/formatadores'
import { Modal } from './Modal'
import { SeletorPessoa } from './SeletorPessoa'

function hoje() {
  const d = new Date()
  return mascaraData(
    `${String(d.getDate()).padStart(2, '0')}${String(d.getMonth() + 1).padStart(2, '0')}${d.getFullYear()}`,
  )
}

/** Cria um atendimento novo (passe `pessoaId`) ou edita um existente (passe `existente`). */
export function AtendimentoModal({ pessoaId, existente, onFechar, onSalvo }) {
  const editando = Boolean(existente)

  const [tipos, setTipos] = useState([])
  const [data, setData] = useState(existente ? isoParaData(existente.data) : hoje())
  const [atendidoPor, setAtendidoPor] = useState(existente?.atendido_por ?? null)
  const [modalidade, setModalidade] = useState(existente?.modalidade ?? 'presencial')
  const [presente, setPresente] = useState(existente?.presente ?? true)
  const [solicitante, setSolicitante] = useState(existente?.solicitante ?? null)
  const [tratamentosMarcados, setTratamentosMarcados] = useState(
    existente ? existente.tratamentos.map((t) => t.tipo_tratamento_id) : [],
  )
  const [observacao, setObservacao] = useState(existente?.observacao ?? '')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    api
      .get('/tipos-tratamento?formato=individual')
      .then(setTipos)
      .catch((e) => setErro(e.message))
  }, [])

  function alternarTratamento(id) {
    setTratamentosMarcados((atual) =>
      atual.includes(id) ? atual.filter((t) => t !== id) : [...atual, id],
    )
  }

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')

    const dataIso = dataParaIso(data)
    if (!dataIso) {
      setErro('Data inválida -- use o formato dd/mm/aaaa.')
      return
    }

    const corpo = {
      data: dataIso,
      atendido_por_id: atendidoPor?.id ?? null,
      modalidade,
      presente,
      solicitante_id: solicitante?.id ?? null,
      observacao: observacao || null,
      tratamentos: tratamentosMarcados.map((id) => ({ tipo_tratamento_id: id })),
    }

    setEnviando(true)
    try {
      if (editando) {
        await api.patch(`/atendimentos/${existente.id}`, corpo)
      } else {
        await api.post('/atendimentos', { ...corpo, pessoa_id: pessoaId })
      }
      onSalvo()
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal titulo={editando ? 'Editar atendimento' : 'Registrar atendimento'} onFechar={onFechar}>
      <form onSubmit={aoEnviar} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-4">
          <Campo label="Data">
            <input
              inputMode="numeric"
              placeholder="dd/mm/aaaa"
              maxLength={10}
              value={data}
              onChange={(e) => setData(mascaraData(e.target.value))}
              className={estiloInput}
            />
          </Campo>
          <Campo label="Modalidade">
            <select
              value={modalidade}
              onChange={(e) => setModalidade(e.target.value)}
              className={estiloInput}
            >
              <option value="presencial">Presencial</option>
              <option value="video">Vídeo</option>
              <option value="distancia">À distância</option>
            </select>
          </Campo>
        </div>

        <Campo label="Atendido por (médium/trabalhador)">
          <SeletorPessoa
            valor={atendidoPor}
            aoSelecionar={setAtendidoPor}
            papel="trabalhador"
            placeholder="Buscar trabalhador..."
          />
        </Campo>

        <label className="flex items-center gap-2 text-sm font-medium text-stone-700">
          <input
            type="checkbox"
            checked={presente}
            onChange={(e) => setPresente(e.target.checked)}
          />
          A pessoa esteve presente
        </label>

        {!presente && (
          <Campo label="Quem trouxe a informação (solicitante)">
            <SeletorPessoa
              valor={solicitante}
              aoSelecionar={setSolicitante}
              placeholder="Buscar pessoa..."
            />
          </Campo>
        )}

        <fieldset>
          <legend className="mb-2 text-sm font-medium text-stone-700">
            Tratamentos do dia
          </legend>
          <div className="grid grid-cols-2 gap-2">
            {tipos.map((t) => (
              <label key={t.id} className="flex items-center gap-2 text-sm text-stone-700">
                <input
                  type="checkbox"
                  checked={tratamentosMarcados.includes(t.id)}
                  onChange={() => alternarTratamento(t.id)}
                />
                {t.nome}
              </label>
            ))}
          </div>
        </fieldset>

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
            {enviando ? 'Salvando...' : editando ? 'Salvar alterações' : 'Registrar'}
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
