import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { Cabecalho } from '../components/Cabecalho'
import { PessoaForm } from '../components/PessoaForm'
import { TituloPagina } from '../components/ui'

export function NovaPessoa() {
  const navigate = useNavigate()

  async function salvar(corpo) {
    const pessoa = await api.post('/pessoas', corpo)
    navigate(`/pessoas/${pessoa.id}`)
  }

  return (
    <div className="min-h-screen bg-stone-100">
      <Cabecalho />

      <main className="mx-auto max-w-3xl px-4 py-6 sm:px-6 sm:py-8">
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-sm text-stone-500 transition hover:text-emerald-800"
        >
          ← Voltar para a lista
        </Link>

        <div className="mt-4">
          <TituloPagina
            titulo="Nova pessoa"
            subtitulo="Preencha a ficha como no papel. Só nome, nascimento, CPF e sexo são obrigatórios."
          />
        </div>

        <div className="mt-6 animate-entrar">
          <PessoaForm aoSalvar={salvar} linkCancelar="/" textoBotao="Salvar ficha" />
        </div>
      </main>
    </div>
  )
}
