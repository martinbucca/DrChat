import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import '@neo4j-ndl/base/lib/neo4j-ds-styles.css';

import ThemeWrapper from './context/ThemeWrapper';

import PageNotFound from './templates/shared/components/PageNotFound';
import ConnectionModal from './templates/shared/components/ConnectionModal';
import Login from './templates/shared/components/Login';
import Dashboard from './pages/Dashboard';

import { FileContextProvider } from './context/connectionFile';

import './ConnectionModal.css';

const isAuthenticated = () => {
  if (typeof window === 'undefined') {
    return false;
  }

  try {
    const stored = window.localStorage.getItem('user');
    if (!stored) {
      return false;
    }

    const parsed = JSON.parse(stored);
    return !!parsed;
  } catch (error) {
    window.localStorage.removeItem('user');
    console.error('Stored user session is invalid', error);
    return false;
  }
};

function RequireAuth({ children }: { children: JSX.Element }) {
  if (!isAuthenticated()) {
    return <Navigate to='/login' replace />;
  }

  return children;
}

function App() {
  return (
    <BrowserRouter>
      <ThemeWrapper>
        <Routes>
          <Route
            path='/'
            element={
              <RequireAuth>
                <Navigate to='/conversations' replace />
              </RequireAuth>
            }
          />

          <Route
            path='/conversations'
            element={
              <RequireAuth>
                <Dashboard />
              </RequireAuth>
            }
          />

          <Route path='/login' element={<Login />} />

          {/* Ruta de conexión real */}
          <Route
            path='/connection'
            element={
              <RequireAuth>
                <FileContextProvider>
                  <ConnectionModal
                    open={true}
                    setOpenConnection={() => null}
                    setConnectionStatus={() => null}
                  />
                </FileContextProvider>
              </RequireAuth>
            }
          />

          {/* 404 */}
          <Route path='*' element={<PageNotFound />} />
        </Routes>
      </ThemeWrapper>
    </BrowserRouter>
  );
}

export default App;
