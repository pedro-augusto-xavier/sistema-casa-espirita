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

/** Cria uma sessão de grupo nova ou edita uma existente (passe `existente`). */
export function GrupoModal({ existente, onFechar, onSalvo }) {
  const editando = Boolean(existente)

  const [tipos, setTipos] = useState([])
  const [tipoId, setTipoId] = useState(existente ? String(existente.tipo_tratamento_id) : '')
  const [data, setData] = useState(existente ? isoParaData(existente.data) : hoje())
  const [responsavel, setResponsavel] = useState(existente?.responsavel ?? null)
  const [presentes, setPresentes] = useState(
    existente ? existente.presencas.map((p) => p.pessoa) : [],
  )
  const [observacao, setObservacao] = useState(existente?.observacao ?? '')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    api
      .get('/tipos-tratamento?formato=grupo')
      .then((lista) => {
        setTipos(lista)
        if (!existente && lista.length > 0) setTipoId(String(lista[0].id))
      })
      .catch((e) => setErro(e.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function adicionarParticipante(pessoa) {
    if (!pessoa || presentes.some((p) => p.id === pessoa.id)) return
    setPresentes((prev) => [...prev, pessoa])
  }

  function removerParticipante(id) {
    setPresentes((prev) => prev.filter((p) => p.id !== id))
  }

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')

    if (!tipoId) {
      setErro('Escolha o tipo de grupo.')
      return
    }
    const dataIso = dataParaIso(data)
    if (!dataIso) {
      setErro('Data inválida -- use o formato dd/mm/aaaa.')
      return
    }

    const corpo = {
      data: dataIso,
      responsavel_id: responsavel?.id ?? null,
      observacao: observacao || null,
      presentes: presentes.map((p) => ({ pessoa_id: p.id })),
    }

    setEnviando(true)
    try {
      if (editando) {
        await api.patch(`/grupos/${existente.id}`, corpo)
      } else {
        await api.post('/grupos', { ...corpo, tipo_tratamento_id: Number(tipoId) })
      }
      onSalvo()
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal titulo={editando ? 'Editar sessão de grupo' : 'Nova sessão de grupo'} onFechar={onFechar}>
      <form onSubmit={aoEnviar} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-4">
          <Campo label="Tipo">
            <select
              value={tipoId}
              onChange={(e) => setTipoId(e.target.value)}
              disabled={editando}
              className={`${estiloInput} disabled:bg-slate-100`}
            >
              {tipos.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.nome}
                </option>
              ))}
            </select>
          </Campo>
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
        </div>

        <Campo label="Responsável (dirigente)">
          <SeletorPessoa
            valor={responsavel}
            aoSelecionar={setResponsavel}
            placeholder="Buscar pessoa..."
          />
        </Campo>

        <fieldset>
          <legend className="mb-2 text-sm font-medium text-slate-700">Presentes</legend>
          {presentes.length > 0 && (
            <ul className="mb-2 flex flex-wrap gap-2">
              {presentes.map((p) => (
                <li
                  key={p.id}
                  className="flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700"
                >
                  {p.nome_completo}
                  <button
                    type="button"
                    onClick={() => removerParticipante(p.id)}
                    className="text-slate-400 hover:text-slate-700"
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          )}
          <SeletorPessoa
            valor={null}
            aoSelecionar={adicionarParticipante}
            placeholder="Adicionar participante..."
          />
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
            {enviando ? 'Salvando...' : editando ? 'Salvar alterações' : 'Registrar'}
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
