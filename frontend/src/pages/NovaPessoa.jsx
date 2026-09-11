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
    <div className="min-h-screen bg-slate-100">
      <header className="bg-white px-6 py-4 shadow-sm">
        <Link to="/" className="text-sm text-slate-500 hover:underline">
          ← Voltar para a lista
        </Link>
        <h1 className="text-lg font-bold text-slate-800">Nova pessoa</h1>
      </header>

      <main className="mx-auto max-w-2xl p-6">
        <PessoaForm aoSalvar={salvar} linkCancelar="/" textoBotao="Salvar" />
      </main>
    </div>
  )
}
