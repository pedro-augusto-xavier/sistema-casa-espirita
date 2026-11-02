import { useAuth } from '../auth/AuthContext'
import { ConfigurarDuasEtapas } from '../components/ConfigurarDuasEtapas'
import { Emblema } from '../components/Emblema'
import { FormTrocarSenha } from '../components/FormTrocarSenha'

/**
 * Aparece no lugar do sistema enquanto a pessoa tiver pendência:
 *   1. trocar a senha provisória (a que o admin definiu, ex: o CPF);
 *   2. configurar a verificação em duas etapas (obrigatória pra admin).
 * A API também bloqueia os dados até isso ser resolvido -- não é só a tela.
 */
export function PrimeiroAcesso() {
  const { usuario, recarregar, sair } = useAuth()
  const pendencias = usuario.pendencias ?? []
  const etapa = pendencias[0]
  const primeiroNome = usuario.nome.split(' ')[0]

  return (
    <div className="flex min-h-screen items-start justify-center bg-linear-to-br from-stone-100 via-emerald-50 to-amber-50 px-4 py-10 sm:items-center">
      <div className="w-full max-w-md animate-entrar">
        <div className="flex flex-col items-center text-center">
          <Emblema className="h-16 w-16" />
          <h1 className="mt-4 font-display text-2xl font-semibold text-emerald-950">
            {etapa === 'trocar_senha' ? `Olá, ${primeiroNome}!` : 'Mais uma proteção'}
          </h1>
          {pendencias.length > 1 && (
            <p className="mt-1 text-xs tracking-wider text-stone-400 uppercase">
              Passo 1 de {pendencias.length}
            </p>
          )}
        </div>

        <div className="mt-6 rounded-2xl bg-white p-6 shadow-xl shadow-emerald-900/10 ring-1 ring-stone-900/5 sm:p-8">
          {etapa === 'trocar_senha' && (
            <>
              <p className="mb-5 text-sm text-stone-600">
                Antes de começar, crie uma senha só sua. A senha que você usou agora era provisória
                e serve só pra este primeiro acesso.
              </p>
              <FormTrocarSenha aoConcluir={recarregar} textoBotao="Salvar minha senha" />
            </>
          )}

          {etapa === 'configurar_mfa' && (
            <>
              <p className="mb-5 text-sm text-stone-600">
                Como você é administrador, o sistema pede uma verificação em duas etapas: além da
                senha, um código do celular. Assim, mesmo que alguém descubra sua senha, não
                consegue entrar.
              </p>
              <ConfigurarDuasEtapas aoConcluir={recarregar} />
            </>
          )}
        </div>

        <button
          type="button"
          onClick={sair}
          className="mt-5 w-full text-center text-xs text-stone-500 hover:text-emerald-800 hover:underline"
        >
          Sair e fazer isso depois
        </button>
      </div>
    </div>
  )
}
