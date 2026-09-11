import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { dataParaIso, mascaraData } from '../utils/formatadores'
import { Modal } from './Modal'
import { SeletorPessoa } from './SeletorPessoa'

function hoje() {
  const d = new Date()
  return mascaraData(
    `${String(d.getDate()).padStart(2, '0')}${String(d.getMonth() + 1).padStart(2, '0')}${d.getFullYear()}`,
  )
}

export function NovoAtendimentoModal({ pessoaId, onFechar, onCriado }) {
  const [tipos, setTipos] = useState([])
  const [data, setData] = useState(hoje())
  const [atendidoPor, setAtendidoPor] = useState(null)
  const [modalidade, setModalidade] = useState('presencial')
  const [tratamentosMarcados, setTratamentosMarcados] = useState([])
  const [observacao, setObservacao] = useState('')
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

    setEnviando(true)
    try {
      await api.post('/atendimentos', {
        pessoa_id: pessoaId,
        data: dataIso,
        atendido_por_id: atendidoPor?.id ?? null,
        modalidade,
        observacao: observacao || null,
        tratamentos: tratamentosMarcados.map((id) => ({ tipo_tratamento_id: id })),
      })
      onCriado()
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal titulo="Registrar atendimento" onFechar={onFechar}>
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

        <fieldset>
          <legend className="mb-2 text-sm font-medium text-slate-700">
            Tratamentos do dia
          </legend>
          <div className="grid grid-cols-2 gap-2">
            {tipos.map((t) => (
              <label key={t.id} className="flex items-center gap-2 text-sm text-slate-700">
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
            className="rounded-md border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={enviando}
            className="rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {enviando ? 'Salvando...' : 'Registrar'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

const estiloInput =
  'w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500'

function Campo({ label, children }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <div className="mt-1">{children}</div>
    </label>
  )
}
