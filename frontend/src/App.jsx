import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import { RotaProtegida } from './auth/RotaProtegida'
import { Auditoria } from './pages/Auditoria'
import { EditarPessoa } from './pages/EditarPessoa'
import { FichaPessoa } from './pages/FichaPessoa'
import { Grupos } from './pages/Grupos'
import { Login } from './pages/Login'
import { NaoEncontrado } from './pages/NaoEncontrado'
import { NovaPessoa } from './pages/NovaPessoa'
import { Pessoas } from './pages/Pessoas'
import { Usuarios } from './pages/Usuarios'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <RotaProtegida>
                <Pessoas />
              </RotaProtegida>
            }
          />
          <Route
            path="/pessoas/nova"
            element={
              <RotaProtegida>
                <NovaPessoa />
              </RotaProtegida>
            }
          />
          <Route
            path="/pessoas/:id"
            element={
              <RotaProtegida>
                <FichaPessoa />
              </RotaProtegida>
            }
          />
          <Route
            path="/pessoas/:id/editar"
            element={
              <RotaProtegida>
                <EditarPessoa />
              </RotaProtegida>
            }
          />
          <Route
            path="/grupos"
            element={
              <RotaProtegida>
                <Grupos />
              </RotaProtegida>
            }
          />
          <Route
            path="/usuarios"
            element={
              <RotaProtegida somenteAdmin>
                <Usuarios />
              </RotaProtegida>
            }
          />
          <Route
            path="/auditoria"
            element={
              <RotaProtegida somenteAdmin>
                <Auditoria />
              </RotaProtegida>
            }
          />
          <Route path="*" element={<NaoEncontrado />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
