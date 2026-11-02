import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { ConfigurarDuasEtapas } from './ConfigurarDuasEtapas'
import { FormTrocarSenha } from './FormTrocarSenha'
import { Modal } from './Modal'
import { Botao, Campo, MensagemErro, Pill } from './ui'

/** "Minha conta": trocar a senha e ligar/desligar a verificação em duas
 * etapas (opcional pra quem não é admin, mas recomendada). */
export function ContaModal({ onFechar }) {
  const { usuario, recarregar } = useAuth()
  const [tela, setTela] = useState('inicio') // inicio | senha | ativar | desativar
  const [aviso, setAviso] = useState('')

  async function concluiu(mensagem) {
    await recarregar()
    setAviso(mensagem)
    setTela('inicio')
  }

  const titulos = {
    inicio: 'Minha conta',
    senha: 'Trocar minha senha',
    ativar: 'Verificação em duas etapas',
    desativar: 'Desligar a verificação em duas etapas',
  }

  return (
    <Modal titulo={titulos[tela]} onFechar={onFechar}>
      {tela === 'inicio' && (
        <div className="flex flex-col gap-4 text-sm">
          {aviso && (
            <p className="rounded-lg bg-emerald-50 px-3 py-2 text-emerald-800 ring-1 ring-emerald-800/10">
              {aviso}
            </p>
          )}

          <section className="flex items-center justify-between gap-3 rounded-xl bg-stone-50 p-4 ring-1 ring-stone-900/5">
            <div>
              <p className="font-medium text-stone-800">Senha</p>
              <p className="text-xs text-stone-500">Ao trocar, os outros aparelhos são desconectados.</p>
            </div>
            <Botao variante="secundario" pequeno onClick={() => setTela('senha')}>
              Trocar
            </Botao>
          </section>

          <section className="flex items-center justify-between gap-3 rounded-xl bg-stone-50 p-4 ring-1 ring-stone-900/5">
            <div>
              <p className="flex items-center gap-2 font-medium text-stone-800">
                Verificação em duas etapas
                <Pill tom={usuario.mfa_ativo ? 'verde' : 'cinza'}>
                  {usuario.mfa_ativo ? 'ligada' : 'desligada'}
                </Pill>
              </p>
              <p className="text-xs text-stone-500">
                {usuario.mfa_obrigatorio
                  ? 'Obrigatória pro seu perfil.'
                  : 'Pede um código do celular além da senha. Recomendado.'}
              </p>
            </div>
            {!usuario.mfa_ativo && (
              <Botao pequeno onClick={() => setTela('ativar')}>
                Ligar
              </Botao>
            )}
            {usuario.mfa_ativo && !usuario.mfa_obrigatorio && (
              <Botao variante="fantasma" pequeno onClick={() => setTela('desativar')}>
                Desligar
              </Botao>
            )}
          </section>

          <Link
            to="/privacidade"
            className="self-start text-xs text-stone-400 underline hover:text-emerald-800"
          >
            Política de privacidade
          </Link>
        </div>
      )}

      {tela === 'senha' && (
        <FormTrocarSenha
          aoConcluir={() => concluiu('Senha trocada. Da próxima vez, entre com a nova.')}
          aoCancelar={() => setTela('inicio')}
        />
      )}

      {tela === 'ativar' && (
        <ConfigurarDuasEtapas
          aoConcluir={() =>
            concluiu('Pronto! A partir de agora o login pede o código do aplicativo.')
          }
          aoCancelar={() => setTela('inicio')}
        />
      )}

      {tela === 'desativar' && (
        <DesativarDuasEtapas
          aoConcluir={() => concluiu('Verificação em duas etapas desligada.')}
          aoCancelar={() => setTela('inicio')}
        />
      )}
    </Modal>
  )
}

function DesativarDuasEtapas({ aoConcluir, aoCancelar }) {
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await api.post('/auth/mfa/desativar', { senha })
      await aoConcluir()
    } catch (e) {
      setErro(e.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={aoEnviar} className="flex flex-col gap-4">
      <p className="text-sm text-stone-600">
        Sua conta fica protegida só pela senha. Confirme com a senha atual.
      </p>
      <Campo label="Senha atual">
        <input
          type="password"
          required
          autoFocus
          autoComplete="current-password"
          value={senha}
          onChange={(e) => setSenha(e.target.value)}
          className="campo"
        />
      </Campo>
      <MensagemErro>{erro}</MensagemErro>
      <div className="flex justify-end gap-2">
        <Botao variante="secundario" type="button" onClick={aoCancelar}>
          Cancelar
        </Botao>
        <Botao variante="perigo" type="submit" disabled={enviando}>
          {enviando ? 'Desligando...' : 'Desligar'}
        </Botao>
      </div>
    </form>
  )
}
