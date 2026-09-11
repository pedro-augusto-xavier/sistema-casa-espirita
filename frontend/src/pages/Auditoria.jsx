import { Fragment, useEffect, useState } from 'react'
import { api } from '../api/client'
import { Cabecalho } from '../components/Cabecalho'

const ROTULO_ACAO = {
  criar: 'Criou',
  atualizar: 'Atualizou',
  excluir: 'Excluiu',
  login: 'Login',
}

const COR_ACAO = {
  criar: 'bg-emerald-100 text-emerald-700',
  atualizar: 'bg-blue-100 text-blue-700',
  excluir: 'bg-red-100 text-red-700',
  login: 'bg-slate-200 text-slate-600',
}

export function Auditoria() {
  const [entidade, setEntidade] = useState('')
  const [pagina, setPagina] = useState(1)
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState('')
  const [aberto, setAberto] = useState(null)

  useEffect(() => {
    const params = new URLSearchParams({ page: pagina, size: 30 })
    if (entidade) params.set('entidade', entidade)
    api
      .get(`/auditoria?${params}`)
      .then(setDados)
      .catch((e) => setErro(e.message))
  }, [entidade, pagina])

  return (
    <div className="min-h-screen bg-slate-100">
      <Cabecalho />

      <main className="mx-auto max-w-4xl p-6">
        <h2 className="text-xl font-bold text-slate-800">Auditoria</h2>
        <p className="text-sm text-slate-500">
          Registro de quem criou, alterou ou excluiu cada coisa no sistema.
        </p>

        <div className="mt-4 flex gap-2">
          <select
            value={entidade}
            onChange={(e) => {
              setPagina(1)
              setEntidade(e.target.value)
            }}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
          >
            <option value="">Todas as entidades</option>
            <option value="pessoa">Pessoa</option>
            <option value="atendimento">Atendimento</option>
            <option value="tratamento">Tratamento</option>
            <option value="usuario">Usuário</option>
          </select>
        </div>

        {erro && (
          <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{erro}</p>
        )}

        <div className="mt-4 overflow-hidden rounded-lg bg-white shadow-sm">
          {!dados ? (
            <p className="p-4 text-sm text-slate-500">Carregando...</p>
          ) : dados.items.length === 0 ? (
            <p className="p-4 text-sm text-slate-500">Nada registrado ainda.</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-4 py-2 font-medium">Quando</th>
                  <th className="px-4 py-2 font-medium">Quem</th>
                  <th className="px-4 py-2 font-medium">Ação</th>
                  <th className="px-4 py-2 font-medium">Entidade</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody>
                {dados.items.map((log) => (
                  <Fragment key={log.id}>
                    <tr className="border-b border-slate-100 last:border-0">
                      <td className="whitespace-nowrap px-4 py-2 text-slate-500">
                        {new Date(log.criado_em).toLocaleString('pt-BR')}
                      </td>
                      <td className="px-4 py-2 text-slate-700">
                        {log.usuario_nome || '—'}
                      </td>
                      <td className="px-4 py-2">
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs ${COR_ACAO[log.acao] || 'bg-slate-100 text-slate-600'}`}
                        >
                          {ROTULO_ACAO[log.acao] || log.acao}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-slate-600">
                        {log.entidade}
                        {log.entidade_id ? ` #${log.entidade_id}` : ''}
                      </td>
                      <td className="px-4 py-2 text-right">
                        {log.dados && (
                          <button
                            onClick={() => setAberto(aberto === log.id ? null : log.id)}
                            className="text-xs text-slate-500 hover:underline"
                          >
                            {aberto === log.id ? 'Ocultar' : 'Detalhes'}
                          </button>
                        )}
                      </td>
                    </tr>
                    {aberto === log.id && (
                      <tr className="border-b border-slate-100 bg-slate-50">
                        <td colSpan={5} className="px-4 py-2">
                          <pre className="overflow-x-auto text-xs text-slate-600">
                            {JSON.stringify(log.dados, null, 2)}
                          </pre>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {dados && dados.pages > 1 && (
          <div className="mt-4 flex items-center justify-center gap-3 text-sm text-slate-600">
            <button
              disabled={pagina <= 1}
              onClick={() => setPagina((p) => p - 1)}
              className="rounded-md border border-slate-300 px-3 py-1 disabled:opacity-40"
            >
              Anterior
            </button>
            <span>
              Página {dados.page} de {dados.pages}
            </span>
            <button
              disabled={pagina >= dados.pages}
              onClick={() => setPagina((p) => p + 1)}
              className="rounded-md border border-slate-300 px-3 py-1 disabled:opacity-40"
            >
              Próxima
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
