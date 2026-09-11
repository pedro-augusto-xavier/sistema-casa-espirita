import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { AtendimentoDetalheModal } from '../components/AtendimentoDetalheModal'
import { NovoAtendimentoModal } from '../components/NovoAtendimentoModal'
import { NovoTratamentoModal } from '../components/NovoTratamentoModal'
import { TratamentoDetalheModal } from '../components/TratamentoDetalheModal'
import { useAuth } from '../auth/AuthContext'
import { isoParaData, mascaraCpf, mascaraTelefone } from '../utils/formatadores'

const ROTULO_TIPO = {
  atendimento: 'Atendimento',
  tratamento_inicio: 'Início de tratamento',
  evolucao: 'Evolução',
}

export function FichaPessoa() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { usuario } = useAuth()

  const [pessoa, setPessoa] = useState(null)
  const [historico, setHistorico] = useState([])
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
      })
      .catch((e) => setErro(e.message))
      .finally(() => setCarregando(false))
  }, [id, versao])

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
            <span>LGPD:</span>
            <button onClick={exportarDados} className="text-slate-600 hover:underline">
              Exportar dados
            </button>
            {usuario.papel === 'admin' && !pessoa.anonimizada && (
              <button onClick={anonimizar} className="text-red-500 hover:underline">
                Anonimizar (apagar dados pessoais)
              </button>
            )}
            {pessoa.anonimizada && <span>dados já anonimizados</span>}
          </div>
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
            <ul className="mt-4 flex flex-col gap-3">
              {historico.map((item, i) => (
                <li key={i} className="border-l-2 border-slate-300 pl-3">
                  <button
                    type="button"
                    onClick={() => abrirDetalhe(item)}
                    className="w-full rounded-md p-1 text-left hover:bg-slate-50"
                  >
                    <div className="flex items-baseline gap-2 text-sm">
                      <span className="font-medium text-slate-700">
                        {ROTULO_TIPO[item.tipo] ?? item.tipo}
                      </span>
                      <span className="text-slate-400">{isoParaData(item.data)}</span>
                    </div>
                    <p className="text-sm text-slate-600">{item.titulo}</p>
                    {item.descricao && (
                      <p className="text-sm text-slate-500">{item.descricao}</p>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>

      {modalAberto === 'atendimento' && (
        <NovoAtendimentoModal
          pessoaId={pessoa.id}
          onFechar={() => setModalAberto(null)}
          onCriado={aoCriarRegistro}
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

function Item({ label, valor }) {
  return (
    <div>
      <dt className="text-xs font-medium text-slate-400">{label}</dt>
      <dd className="text-slate-700">{valor || '—'}</dd>
    </div>
  )
}
