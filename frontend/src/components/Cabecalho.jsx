import { useEffect, useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Emblema } from './Emblema'
import { ContaModal } from './ContaModal'
import { Avatar, Botao } from './ui'

function ItemNav({ to, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `relative px-1 py-1 text-sm transition ${
          isActive
            ? 'font-semibold text-emerald-900 after:absolute after:inset-x-0 after:-bottom-1 after:h-0.5 after:rounded-full after:bg-emerald-700'
            : 'text-stone-500 hover:text-emerald-800'
        }`
      }
    >
      {children}
    </NavLink>
  )
}

export function Cabecalho() {
  const { usuario, sair } = useAuth()
  const [contaAberta, setContaAberta] = useState(false)
  const [alerta, setAlerta] = useState(false)
  const ehAdmin = usuario.papel === 'admin'

  // admin vê um aviso na Auditoria quando tem algo estranho (muitas senhas
  // erradas, acesso de madrugada...)
  useEffect(() => {
    if (!ehAdmin) return
    api
      .get('/auditoria/alertas')
      .then((a) => setAlerta(a.alerta))
      .catch(() => {})
  }, [ehAdmin])

  return (
    <>
      <header className="sticky top-0 z-10 bg-white/90 shadow-sm ring-1 ring-stone-900/5 backdrop-blur">
        <div className="h-1 bg-linear-to-r from-emerald-800 via-emerald-600 to-amber-500" />
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-x-6 gap-y-3 px-4 py-3 sm:px-6">
          <div className="flex flex-wrap items-center gap-x-8 gap-y-2">
            <Link to="/" className="flex items-center gap-3">
              <Emblema className="h-10 w-10 shrink-0" />
              <span className="flex flex-col leading-tight">
                <span className="font-display text-base font-semibold text-emerald-950 sm:text-lg">
                  Casa Espírita Amor e Perdão
                </span>
                <span className="text-[10px] font-medium tracking-[0.2em] text-stone-400 uppercase">
                  Nova Friburgo · RJ
                </span>
              </span>
            </Link>

            <nav className="flex flex-wrap items-center gap-x-5 gap-y-1">
              <ItemNav to="/">Pessoas</ItemNav>
              <ItemNav to="/agenda">Agenda</ItemNav>
              {ehAdmin && (
                <>
                  <ItemNav to="/usuarios">Usuários</ItemNav>
                  <ItemNav to="/auditoria">
                    Auditoria
                    {alerta && (
                      <span
                        title="Tem algo pra conferir na auditoria"
                        className="ml-1 inline-block h-2 w-2 rounded-full bg-red-500 align-top"
                      />
                    )}
                  </ItemNav>
                </>
              )}
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Avatar nome={usuario.nome} className="h-8 w-8 text-xs" />
              <span className="hidden flex-col leading-tight sm:flex">
                <span className="text-sm font-medium text-stone-700">{usuario.nome}</span>
                <span className="text-[10px] tracking-wider text-stone-400 uppercase">
                  {usuario.papel}
                </span>
              </span>
            </div>
            <Botao variante="secundario" pequeno onClick={() => setContaAberta(true)}>
              Minha conta
            </Botao>
            <Botao variante="secundario" pequeno onClick={sair}>
              Sair
            </Botao>
          </div>
        </div>
      </header>

      {/* fora do header: o backdrop-blur dele prenderia o modal (position: fixed) na faixa do topo */}
      {contaAberta && <ContaModal onFechar={() => setContaAberta(false)} />}
    </>
  )
}
