import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import { RotaProtegida } from './auth/RotaProtegida'
import { EditarPessoa } from './pages/EditarPessoa'
import { FichaPessoa } from './pages/FichaPessoa'
import { Login } from './pages/Login'
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
            path="/usuarios"
            element={
              <RotaProtegida somenteAdmin>
                <Usuarios />
              </RotaProtegida>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
