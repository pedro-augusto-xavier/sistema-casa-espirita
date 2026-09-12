import { useState } from 'react'
import { api } from '../api/client'
import { Modal } from './Modal'
import { SeletorPessoa } from './SeletorPessoa'

const TIPOS = [
  { valor: 'trabalho', rotulo: 'Trabalho' },
  { valor: 'palestra', rotulo: 'Palestra' },
  { valor: 'grupo', rotulo: 'Grupo' },
  { valor: 'outro', rotulo: 'Outro' },
]

function paraDatetimeLocal(iso) {
  if (!iso) return ''
  return iso.slice(0, 16) // "2026-06-30T19:00:00-03:00" -> "2026-06-30T19:00"
}

/** Cria um evento de agenda novo ou edita um existente (passe `existente`). */
export function AgendaModal({ existente, onFechar, onSalvo }) {
  const editando = Boolean(existente)

  const [titulo, setTitulo] = useState(existente?.titulo ?? '')
  const [tipo, setTipo] = useState(existente?.tipo ?? 'trabalho')
  const [dataInicio, setDataInicio] = useState(paraDatetimeLocal(existente?.data_inicio))
  const [dataFim, setDataFim] = useState(paraDatetimeLocal(existente?.data_fim))
  const [recorrencia, setRecorrencia] = useState(existente?.recorrencia ?? '')
  const [descricao, setDescricao] = useState(existente?.descricao ?? '')
  const [escalados, setEscalados] = useState(
    existente ? existente.escalas.map((e) => ({ pessoa: e.pessoa, funcao: e.funcao ?? '' })) : [],
  )
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  function adicionarEscalado(pessoa) {
    if (!pessoa || escalados.some((e) => e.pessoa.id === pessoa.id)) return
    setEscalados((prev) => [...prev, { pessoa, funcao: '' }])
  }

  function mudarFuncao(pessoaId, funcao) {
    setEscalados((prev) =>
      prev.map((e) => (e.pessoa.id === pessoaId ? { ...e, funcao } : e)),
    )
  }

  function removerEscalado(pessoaId) {
    setEscalados((prev) => prev.filter((e) => e.pessoa.id !== pessoaId))
  }

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')

    if (!dataInicio) {
      setErro('Informe a data e hora de início.')
      return
    }

    const corpo = {
      titulo,
      tipo,
      data_inicio: dataInicio,
      data_fim: dataFim || null,
      recorrencia: recorrencia || null,
      descricao: descricao || null,
      escalados: escalados.map((e) => ({
        pessoa_id: e.pessoa.id,
        funcao: e.funcao || null,
      })),
    }

    setEnviando(true)
    try {
      if (editando) {
        await api.patch(`/agenda/${existente.id}`, corpo)
      } else {
        await api.post('/agenda', corpo)
      }
      onSalvo()
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal titulo={editando ? 'Editar evento' : 'Novo evento na agenda'} onFechar={onFechar}>
      <form onSubmit={aoEnviar} className="flex flex-col gap-4">
        <Campo label="Título">
          <input
            required
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            className={estiloInput}
          />
        </Campo>

        <div className="grid grid-cols-2 gap-4">
          <Campo label="Tipo">
            <select value={tipo} onChange={(e) => setTipo(e.target.value)} className={estiloInput}>
              {TIPOS.map((t) => (
                <option key={t.valor} value={t.valor}>
                  {t.rotulo}
                </option>
              ))}
            </select>
          </Campo>
          <Campo label="Recorrência (opcional)">
            <input
              placeholder="ex: semanal:terça"
              value={recorrencia}
              onChange={(e) => setRecorrencia(e.target.value)}
              className={estiloInput}
            />
          </Campo>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Campo label="Início">
            <input
              required
              type="datetime-local"
              value={dataInicio}
              onChange={(e) => setDataInicio(e.target.value)}
              className={estiloInput}
            />
          </Campo>
          <Campo label="Fim (opcional)">
            <input
              type="datetime-local"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
              className={estiloInput}
            />
          </Campo>
        </div>

        <fieldset>
          <legend className="mb-2 text-sm font-medium text-stone-700">Escala</legend>
          {escalados.length > 0 && (
            <ul className="mb-2 flex flex-col gap-2">
              {escalados.map((e) => (
                <li key={e.pessoa.id} className="flex items-center gap-2">
                  <span className="flex-1 text-sm text-stone-700">{e.pessoa.nome_completo}</span>
                  <input
                    placeholder="função (opcional)"
                    value={e.funcao}
                    onChange={(ev) => mudarFuncao(e.pessoa.id, ev.target.value)}
                    className="w-40 rounded-md border border-stone-300 px-2 py-1 text-xs outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/15"
                  />
                  <button
                    type="button"
                    onClick={() => removerEscalado(e.pessoa.id)}
                    className="text-stone-400 hover:text-stone-700"
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          )}
          <SeletorPessoa
            valor={null}
            aoSelecionar={adicionarEscalado}
            placeholder="Adicionar pessoa à escala..."
          />
        </fieldset>

        <Campo label="Descrição">
          <textarea
            rows={2}
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
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
            {enviando ? 'Salvando...' : editando ? 'Salvar alterações' : 'Criar evento'}
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
