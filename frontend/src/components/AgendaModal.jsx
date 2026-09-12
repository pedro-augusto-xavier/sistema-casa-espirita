import { useState } from 'react'
import { api } from '../api/client'
import { Modal } from './Modal'
import { SeletorPessoa } from './SeletorPessoa'
import { Avatar, Botao, Campo, MensagemErro } from './ui'

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
            autoFocus
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            className="campo"
            placeholder="ex: Reunião pública de terça"
          />
        </Campo>

        <div className="grid grid-cols-2 gap-4">
          <Campo label="Tipo">
            <select value={tipo} onChange={(e) => setTipo(e.target.value)} className="campo">
              {TIPOS.map((t) => (
                <option key={t.valor} value={t.valor}>
                  {t.rotulo}
                </option>
              ))}
            </select>
          </Campo>
          <Campo label="Recorrência" dica="opcional">
            <input
              placeholder="ex: semanal:terça"
              value={recorrencia}
              onChange={(e) => setRecorrencia(e.target.value)}
              className="campo"
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
              className="campo"
            />
          </Campo>
          <Campo label="Fim" dica="opcional">
            <input
              type="datetime-local"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
              className="campo"
            />
          </Campo>
        </div>

        <fieldset>
          <legend className="mb-2 flex items-baseline gap-2 text-sm font-medium text-stone-700">
            Escala
            {escalados.length > 0 && (
              <span className="text-xs font-normal text-stone-400">{escalados.length}</span>
            )}
          </legend>
          {escalados.length > 0 && (
            <ul className="mb-2 flex flex-col gap-1.5">
              {escalados.map((e) => (
                <li
                  key={e.pessoa.id}
                  className="flex items-center gap-2 rounded-lg bg-stone-50 py-1.5 pr-1.5 pl-2 ring-1 ring-stone-900/5"
                >
                  <Avatar nome={e.pessoa.nome_completo} className="h-7 w-7 text-[10px]" />
                  <span className="min-w-0 flex-1 truncate text-sm text-stone-800">
                    {e.pessoa.nome_completo}
                  </span>
                  <input
                    placeholder="função"
                    value={e.funcao}
                    onChange={(ev) => mudarFuncao(e.pessoa.id, ev.target.value)}
                    className="campo w-32 px-2 py-1 text-xs"
                  />
                  <button
                    type="button"
                    onClick={() => removerEscalado(e.pessoa.id)}
                    aria-label={`Remover ${e.pessoa.nome_completo}`}
                    className="flex h-7 w-7 items-center justify-center rounded-md text-stone-400 hover:bg-white hover:text-red-600"
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
            className="campo"
          />
        </Campo>

        <MensagemErro>{erro}</MensagemErro>

        <div className="flex justify-end gap-2 pt-1">
          <Botao variante="secundario" onClick={onFechar}>
            Cancelar
          </Botao>
          <Botao type="submit" disabled={enviando}>
            {enviando ? 'Salvando...' : editando ? 'Salvar alterações' : 'Criar evento'}
          </Botao>
        </div>
      </form>
    </Modal>
  )
}
