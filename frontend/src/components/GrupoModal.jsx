import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { dataParaIso, isoParaData, mascaraData } from '../utils/formatadores'
import { Modal } from './Modal'
import { SeletorPessoa } from './SeletorPessoa'
import { Avatar, Botao, Campo, MensagemErro } from './ui'

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
      setErro('Data inválida — use o formato dd/mm/aaaa.')
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
    <Modal
      titulo={editando ? 'Editar sessão de grupo' : 'Nova sessão de grupo'}
      onFechar={onFechar}
    >
      <form onSubmit={aoEnviar} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-4">
          <Campo label="Tipo">
            <select
              value={tipoId}
              onChange={(e) => setTipoId(e.target.value)}
              disabled={editando}
              className="campo"
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
              className="campo"
            />
          </Campo>
        </div>

        <Campo label="Responsável" dica="dirigente">
          <SeletorPessoa
            valor={responsavel}
            aoSelecionar={setResponsavel}
            placeholder="Buscar pessoa..."
          />
        </Campo>

        <fieldset>
          <legend className="mb-2 flex items-baseline gap-2 text-sm font-medium text-stone-700">
            Presentes
            {presentes.length > 0 && (
              <span className="text-xs font-normal text-stone-400">{presentes.length}</span>
            )}
          </legend>
          {presentes.length > 0 && (
            <ul className="mb-2 flex flex-wrap gap-1.5">
              {presentes.map((p) => (
                <li
                  key={p.id}
                  className="flex items-center gap-1.5 rounded-full bg-emerald-50 py-0.5 pr-1 pl-0.5 text-xs text-emerald-950 ring-1 ring-emerald-800/10"
                >
                  <Avatar nome={p.nome_completo} className="h-5 w-5 text-[8px]" />
                  {p.nome_completo}
                  <button
                    type="button"
                    onClick={() => removerParticipante(p.id)}
                    aria-label={`Remover ${p.nome_completo}`}
                    className="flex h-4 w-4 items-center justify-center rounded-full text-stone-400 hover:bg-white hover:text-red-600"
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
            permitirCadastro
          />
        </fieldset>

        <Campo label="Observação">
          <textarea
            rows={2}
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
            {enviando ? 'Salvando...' : editando ? 'Salvar alterações' : 'Registrar'}
          </Botao>
        </div>
      </form>
    </Modal>
  )
}
