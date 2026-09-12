import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { AtendimentoDetalheModal } from '../components/AtendimentoDetalheModal'
import { AtendimentoModal } from '../components/AtendimentoModal'
import { NovoTratamentoModal } from '../components/NovoTratamentoModal'
import { TratamentoDetalheModal } from '../components/TratamentoDetalheModal'
import { useAuth } from '../auth/AuthContext'
import { isoParaData, mascaraCpf, mascaraTelefone } from '../utils/formatadores'

const ROTULO_TIPO = {
  atendimento: 'Atendimento',
  tratamento_inicio: 'Início de tratamento',
  evolucao: 'Evolução',
  grupo: 'Grupo',
}

const ROTULO_MODALIDADE = {
  presencial: 'Presencial',
  video: 'Vídeo',
  distancia: 'À distância',
}

export function FichaPessoa() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { usuario } = useAuth()

  const [pessoa, setPessoa] = useState(null)
  const [historico, setHistorico] = useState([])
  const [edicoes, setEdicoes] = useState([])
  const [mostrarEdicoes, setMostrarEdicoes] = useState(false)
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(true)
  const [modalAberto, setModalAberto] = useState(null) // 'atendimento' | 'tratamento' | null
  const [detalhe, setDetalhe] = useState(null) // { tipo: 'atendimento' | 'tratamento', id }
  const [versao, setVersao] = useState(0)

  useEffect(() => {
    setCarregando(true)
    setErro('')
    Promise.all([api.get(`/pessoas/${id}`), api.get(`/pessoas/${id}/historico`)])
      .then(([p, h]) => {
        setPessoa(p)
        setHistorico(h)
        if (p && usuario.papel === 'admin') {
          api
            .get(`/auditoria?entidade=pessoa&entidade_id=${id}&size=50`)
            .then((d) => setEdicoes(d.items))
            .catch(() => {})
        }
      })
      .catch((e) => setErro(e.message))
      .finally(() => setCarregando(false))
  }, [id, versao, usuario.papel])

  function aoCriarRegistro() {
    setModalAberto(null)
    setVersao((v) => v + 1)
  }

  function abrirDetalhe(item) {
    if (item.tipo === 'atendimento' && item.atendimento_id) {
      setDetalhe({ tipo: 'atendimento', id: item.atendimento_id })
    } else if (item.tratamento_id) {
      setDetalhe({ tipo: 'tratamento', id: item.tratamento_id })
    }
  }

  function fecharDetalhe() {
    setDetalhe(null)
    setVersao((v) => v + 1) // pode ter mudado algo (evolução, assistido concluído)
  }

  async function desativar() {
    if (!confirm(`Desativar a ficha de ${pessoa.nome_completo}?`)) return
    try {
      await api.del(`/pessoas/${id}`)
      navigate('/')
    } catch (e) {
      setErro(e.message)
    }
  }

  async function exportarDados() {
    try {
      const dados = await api.get(`/pessoas/${id}/exportar`)
      const blob = new Blob([JSON.stringify(dados, null, 2)], {
        type: 'application/json',
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `ficha-${pessoa.nome_completo.replace(/\s+/g, '_')}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setErro(e.message)
    }
  }

  async function anonimizar() {
    if (
      !confirm(
        `Isso apaga os dados pessoais de ${pessoa.nome_completo} (CPF, telefone, endereço...) e não pode ser desfeito. O histórico de atendimentos é mantido. Continuar?`,
      )
    )
      return
    try {
      await api.post(`/pessoas/${id}/anonimizar`)
      setVersao((v) => v + 1)
    } catch (e) {
      setErro(e.message)
    }
  }

  if (carregando) {
    return <p className="p-6 text-sm text-slate-500">Carregando...</p>
  }

  if (erro && !pessoa) {
    return <p className="p-6 text-sm text-red-600">{erro}</p>
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-white px-6 py-4 shadow-sm">
        <Link to="/" className="text-sm text-slate-500 hover:underline">
          ← Voltar para a lista
        </Link>
      </header>

      <main className="mx-auto max-w-3xl p-6">
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-xl font-bold text-slate-800">
                {pessoa.nome_completo}
              </h1>
              <p className="text-sm text-slate-500">
                {pessoa.papeis.length > 0 ? pessoa.papeis.join(', ') : 'sem papel definido'}
                {!pessoa.ativo && (
                  <span className="ml-2 rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-600">
                    inativa
                  </span>
                )}
              </p>
            </div>
            <div className="flex gap-2">
              <Link
                to={`/pessoas/${id}/editar`}
                className="rounded-md border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50"
              >
                Editar
              </Link>
              {pessoa.ativo && (
                <button
                  onClick={desativar}
                  className="rounded-md border border-red-200 px-3 py-1 text-sm text-red-600 hover:bg-red-50"
                >
                  Desativar
                </button>
              )}
            </div>
          </div>

          <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <Item label="Nascimento" valor={isoParaData(pessoa.data_nascimento)} />
            <Item label="Telefone" valor={pessoa.telefone && mascaraTelefone(pessoa.telefone)} />
            <Item label="CPF" valor={pessoa.cpf && mascaraCpf(pessoa.cpf)} />
            <Item label="Como conheceu" valor={pessoa.como_conheceu} />
            <Item
              label="Endereço"
              valor={[
                pessoa.logradouro,
                pessoa.numero,
                pessoa.bairro,
                pessoa.cidade && pessoa.uf ? `${pessoa.cidade}/${pessoa.uf}` : pessoa.cidade,
              ]
                .filter(Boolean)
                .join(', ')}
            />
            <Item label="CEP" valor={pessoa.cep} />
          </dl>

          {pessoa.observacoes_gerais && (
            <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-600">
              {pessoa.observacoes_gerais}
            </p>
          )}

          <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-slate-100 pt-4 text-xs text-slate-400">
            <button
              onClick={async () => {
                const { gerarPdfFicha } = await import('../utils/gerarPdfFicha')
                gerarPdfFicha(pessoa, historico)
              }}
              className="text-slate-600 hover:underline"
            >
              Baixar PDF
            </button>
            <span>LGPD:</span>
            <button onClick={exportarDados} className="text-slate-600 hover:underline">
              Exportar dados (JSON)
            </button>
            {usuario.papel === 'admin' && !pessoa.anonimizada && (
              <button onClick={anonimizar} className="text-red-500 hover:underline">
                Anonimizar (apagar dados pessoais)
              </button>
            )}
            {pessoa.anonimizada && <span>dados já anonimizados</span>}
            {usuario.papel === 'admin' && edicoes.length > 0 && (
              <button
                onClick={() => setMostrarEdicoes((v) => !v)}
                className="text-slate-600 hover:underline"
              >
                {mostrarEdicoes ? 'Ocultar' : 'Quem editou esta ficha'}
              </button>
            )}
          </div>

          {mostrarEdicoes && (
            <ul className="mt-2 flex flex-col gap-1.5 border-t border-slate-100 pt-2 text-xs text-slate-500">
              {edicoes.map((e) => (
                <li key={e.id}>
                  <span className="font-medium text-slate-700">
                    {e.usuario_nome || 'sistema'}
                  </span>{' '}
                  {e.acao === 'criar' ? 'criou a ficha' : 'alterou a ficha'} em{' '}
                  {new Date(e.criado_em).toLocaleString('pt-BR')}
                  {e.dados && Object.keys(e.dados).length > 0 && (
                    <ul className="ml-4 mt-0.5 list-disc text-slate-400">
                      {Object.entries(e.dados).map(([campo, valor]) => (
                        <li key={campo}>{formatarAlteracao(campo, valor)}</li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="mt-6 rounded-lg bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-800">Histórico</h2>
            <div className="flex gap-2">
              <button
                onClick={() => setModalAberto('atendimento')}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
              >
                + Atendimento
              </button>
              <button
                onClick={() => setModalAberto('tratamento')}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
              >
                + Tratamento
              </button>
            </div>
          </div>

          {erro && <p className="mt-2 text-sm text-red-600">{erro}</p>}

          {historico.length === 0 ? (
            <p className="mt-2 text-sm text-slate-500">
              Nenhum atendimento ou tratamento registrado ainda.
            </p>
          ) : (
            <ul className="mt-4 flex flex-col divide-y divide-slate-100">
              {historico.map((item, i) => (
                <LinhaHistorico
                  key={i}
                  item={item}
                  aoEditar={
                    item.atendimento_id || item.tratamento_id
                      ? () => abrirDetalhe(item)
                      : null
                  }
                />
              ))}
            </ul>
          )}
        </div>
      </main>

      {modalAberto === 'atendimento' && (
        <AtendimentoModal
          pessoaId={pessoa.id}
          onFechar={() => setModalAberto(null)}
          onSalvo={aoCriarRegistro}
        />
      )}
      {modalAberto === 'tratamento' && (
        <NovoTratamentoModal
          pessoaId={pessoa.id}
          onFechar={() => setModalAberto(null)}
          onCriado={aoCriarRegistro}
        />
      )}

      {detalhe?.tipo === 'atendimento' && (
        <AtendimentoDetalheModal atendimentoId={detalhe.id} onFechar={fecharDetalhe} />
      )}
      {detalhe?.tipo === 'tratamento' && (
        <TratamentoDetalheModal tratamentoId={detalhe.id} onFechar={fecharDetalhe} />
      )}
    </div>
  )
}

function formatarValor(v) {
  if (v === null || v === undefined || v === '') return '(vazio)'
  if (Array.isArray(v)) return v.join(', ') || '(vazio)'
  return String(v)
}

/** "campo: de → para" quando dá pra comparar; senão só mostra o valor. */
function formatarAlteracao(campo, valor) {
  if (valor && typeof valor === 'object' && 'de' in valor && 'para' in valor) {
    return `${campo}: ${formatarValor(valor.de)} → ${formatarValor(valor.para)}`
  }
  return `${campo}: ${formatarValor(valor)}`
}

function Item({ label, valor }) {
  return (
    <div>
      <dt className="text-xs font-medium text-slate-400">{label}</dt>
      <dd className="text-slate-700">{valor || '—'}</dd>
    </div>
  )
}

/** Uma linha do histórico, no estilo da ficha de papel: data em destaque
 * e todos os campos daquele tipo já visíveis, sem precisar clicar. */
function LinhaHistorico({ item, aoEditar }) {
  const d = item.detalhes ?? {}

  return (
    <li className="py-3 first:pt-0 last:pb-0">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-baseline gap-2">
          <span className="font-bold text-slate-800">{isoParaData(item.data)}</span>
          <span className="text-sm font-medium text-slate-500">
            {ROTULO_TIPO[item.tipo] ?? item.tipo}
          </span>
        </div>
        {aoEditar && (
          <button
            onClick={aoEditar}
            className="shrink-0 text-xs text-slate-500 hover:text-slate-800 hover:underline"
          >
            {item.tipo === 'atendimento' ? 'Editar' : 'Ver caso'}
          </button>
        )}
      </div>

      <div className="mt-1 flex flex-col gap-0.5 text-sm text-slate-600">
        {item.tipo === 'atendimento' && (
          <>
            <p>
              {ROTULO_MODALIDADE[d.modalidade] ?? d.modalidade}
              {d.presente === false && ' · não esteve presente'}
            </p>
            {d.atendido_por && <p>Atendido por: {d.atendido_por}</p>}
            {d.solicitante && <p>Solicitante: {d.solicitante}</p>}
            {d.tratamentos?.length > 0 && (
              <p>
                Tratamentos:{' '}
                {d.tratamentos
                  .map(
                    (t) =>
                      t.nome +
                      (t.sessoes_previstas
                        ? ` (${t.sessoes_realizadas}/${t.sessoes_previstas} sessões)`
                        : ''),
                  )
                  .join('; ')}
              </p>
            )}
            {d.observacao && <p className="italic text-slate-500">"{d.observacao}"</p>}
          </>
        )}

        {item.tipo === 'tratamento_inicio' && (
          <>
            <p className="font-medium text-slate-700">{d.tipo_nome}</p>
            {d.solicitante && <p>Responsável: {d.solicitante}</p>}
            {d.sessoes_previstas != null && <p>{d.sessoes_previstas} sessões previstas</p>}
            {d.observacao && <p className="italic text-slate-500">"{d.observacao}"</p>}
          </>
        )}

        {item.tipo === 'evolucao' && (
          <>
            <p className="text-xs uppercase tracking-wide text-slate-400">{d.tipo_nome}</p>
            <p className="italic">
              "{d.texto}"{d.registrado_por && ` — ${d.registrado_por}`}
            </p>
          </>
        )}

        {item.tipo === 'grupo' && (
          <>
            <p className="font-medium text-slate-700">{d.tipo_nome}</p>
            {d.responsavel && <p>Responsável: {d.responsavel}</p>}
            {d.observacao && <p className="italic text-slate-500">"{d.observacao}"</p>}
          </>
        )}
      </div>
    </li>
  )
}
