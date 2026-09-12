import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { PessoaForm } from '../components/PessoaForm'

export function NovaPessoa() {
  const navigate = useNavigate()

  async function salvar(corpo) {
    const pessoa = await api.post('/pessoas', corpo)
    navigate(`/pessoas/${pessoa.id}`)
  }

  return (
    <div className="min-h-screen bg-stone-100">
      <header className="bg-white px-6 py-4 shadow-sm ring-1 ring-stone-900/5">
        <Link to="/" className="text-sm text-stone-500 hover:underline">
          ← Voltar para a lista
        </Link>
        <h1 className="font-display text-xl font-semibold text-emerald-900">Nova pessoa</h1>
      </header>

      <main className="mx-auto max-w-2xl p-6">
        <PessoaForm aoSalvar={salvar} linkCancelar="/" textoBotao="Salvar" />
      </main>
    </div>
  )
}
