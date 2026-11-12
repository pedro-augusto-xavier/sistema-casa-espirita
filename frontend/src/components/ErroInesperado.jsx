import { Component } from 'react'
import { Emblema } from './Emblema'

// Pega erro de tela (bug no React) pra não deixar a página toda em branco.
// Fica por fora do roteador, então o botão recarrega a página inteira.
export class ErroInesperado extends Component {
  state = { erro: null }

  static getDerivedStateFromError(erro) {
    return { erro }
  }

  componentDidCatch(erro, info) {
    console.error(erro, info.componentStack)
  }

  render() {
    if (!this.state.erro) return this.props.children
    return (
      <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-linear-to-br from-stone-100 via-emerald-50 to-amber-50 px-4">
        <div className="relative flex max-w-md flex-col items-center text-center">
          <Emblema className="h-20 w-20 opacity-60 grayscale" />
          <p className="mt-6 font-display text-3xl font-semibold text-emerald-950">
            Algo deu errado nesta tela
          </p>
          <p className="mt-2 text-stone-500">
            Nada do que já estava salvo foi perdido. Recarregue a página e tente de novo; se
            continuar, avise quem cuida do sistema.
          </p>
          <button
            type="button"
            className="btn btn-primario mt-6"
            onClick={() => window.location.assign('/')}
          >
            Recarregar
          </button>
        </div>
      </div>
    )
  }
}
