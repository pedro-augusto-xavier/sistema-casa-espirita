import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { dataParaIso, isoParaData, mascaraData } from '../utils/formatadores'
import { Modal } from './Modal'
import { SeletorPessoa } from './SeletorPessoa'
import { Botao, Campo, MensagemErro } from './ui'

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
      setErro('Data inválida — use o formato dd/mm/aaaa.')
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
              className="campo"
            />
          </Campo>
          <Campo label="Modalidade">
            <select
              value={modalidade}
              onChange={(e) => setModalidade(e.target.value)}
              className="campo"
            >
              <option value="presencial">Presencial</option>
              <option value="video">Vídeo</option>
              <option value="distancia">À distância</option>
            </select>
          </Campo>
        </div>

        <Campo label="Atendido por" dica="médium / trabalhador">
          <SeletorPessoa
            valor={atendidoPor}
            aoSelecionar={setAtendidoPor}
            papel="trabalhador"
            placeholder="Buscar trabalhador..."
          />
        </Campo>

        <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-stone-200 px-3 py-2 text-sm text-stone-700 select-none hover:bg-stone-50">
          <input
            type="checkbox"
            checked={presente}
            onChange={(e) => setPresente(e.target.checked)}
            className="accent-emerald-700"
          />
          A pessoa esteve presente
        </label>

        {!presente && (
          <div className="animate-surgir">
            <Campo label="Quem trouxe a informação" dica="solicitante">
              <SeletorPessoa
                valor={solicitante}
                aoSelecionar={setSolicitante}
                placeholder="Buscar pessoa..."
              />
            </Campo>
          </div>
        )}

        <fieldset>
          <legend className="mb-2 text-sm font-medium text-stone-700">Tratamentos do dia</legend>
          <div className="flex flex-wrap gap-1.5">
            {tipos.map((t) => {
              const marcado = tratamentosMarcados.includes(t.id)
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => alternarTratamento(t.id)}
                  aria-pressed={marcado}
                  className={`rounded-full px-3 py-1 text-sm transition ${
                    marcado
                      ? 'bg-emerald-800 font-medium text-white shadow-sm'
                      : 'bg-white text-stone-600 ring-1 ring-stone-900/10 hover:bg-stone-50'
                  }`}
                >
                  {marcado ? '✓ ' : ''}
                  {t.nome}
                </button>
              )
            })}
          </div>
        </fieldset>

        <Campo label="Observação">
          <textarea
            rows={3}
            value={observacao}
            onChange={(e) => setObservacao(e.target.value)}
            className="campo"
            placeholder="O que foi conversado, orientações, encaminhamentos..."
          />
        </Campo>

        <MensagemErro>{erro}</MensagemErro>

        <div className="flex justify-end gap-2 pt-1">
          <Botao variante="secundario" onClick={onFechar}>
            Cancelar
          </Botao>
          <Botao type="submit" disabled={enviando}>
            {enviando ? 'Salvando...' : editando ? 'Salvar alterações' : 'Registrar'}
          </Botao>
        </div>
      </form>
    </Modal>
  )
}
