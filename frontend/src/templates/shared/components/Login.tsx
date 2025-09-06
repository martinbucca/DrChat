// src/pages/Login.tsx
import { useEffect, useState } from 'react';
import { Button, Widget, Tabs } from '@neo4j-ndl/react';
import { useNavigate } from 'react-router-dom';
import Header from './Header';
import DrChatLogo from '../assets/dr_chat_logo.png';
import axios from 'axios';

export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<'login' | 'register'>('login');

  const [email, setEmail] = useState('');
  const [name, setName] = useState('');          // solo registro
  const [password, setPassword] = useState('');  // requerido en ambos
  const [profession, setProfession] = useState(''); // solo registro

  useEffect(() => {
    const user = localStorage.getItem('user');
    if (user) navigate('/', { replace: true });
  }, [navigate]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email.trim() || !password.trim()) return;
    if (mode === 'register' && (!name.trim() || !profession.trim())) return;

    try {
      const base = (import.meta as any).env.VITE_USER_API_URL || 'http://localhost:5002';
      if (mode === 'register') {
        const res = await axios.post(`${base}/api/register`, {
          name,
          email,
          password,
          profesion: profession,
        });
        localStorage.setItem('user', JSON.stringify(res.data));
      } else {
        const res = await axios.post(`${base}/api/login`, { email, password });
        localStorage.setItem('user', JSON.stringify(res.data));
      }
      navigate('/', { replace: true });
    } catch (err) {
      console.error('Auth error', err);
      alert('Error de autenticación');
    }
  };

  return (
    <>
      <Header title="DrChat" userHeader={false} />
      <div className="n-bg-palette-neutral-bg-default min-h-[calc(100vh-64px)] flex items-center justify-center px-4 py-10">
        <Widget className="w-full max-w-6xl rounded-3xl overflow-hidden shadow-2xl" isElevated>
          <div className="grid grid-cols-1 lg:grid-cols-2">
            {/* Panel izquierdo gris */}
            <div className="hidden lg:flex items-center justify-center p-12 bg-neutral-100 dark:bg-neutral-800">
              <div className="flex flex-col items-center text-center text-neutral-800 dark:text-neutral-100">
                <div className="rounded-2xl bg-white/70 dark:bg-white/10 backdrop-blur p-6 shadow-lg">
                  <img src={DrChatLogo} alt="DrChat" className="h-20 w-20 object-contain" />
                </div>
                <h2 className="mt-8 text-3xl font-semibold">Aca algo 1 y con otro logo mas lindo creo</h2>
                <p className="mt-2 max-w-sm opacity-80">Aca algo 2</p>
              </div>
            </div>

            {/* Panel derecho: tabs + form */}
            <div className="bg-neutral-900 text-white px-8 py-10 lg:px-16 lg:py-16 flex items-center justify-center">
              <div className="w-full max-w-md">
                {/* Tabs */}
                <div className="flex justify-center">
                  <Tabs
                    size="large"
                    fill="underline"
                    value={mode}
                    onChange={(val) => setMode(val as 'login' | 'register')}
                  >
                    <Tabs.Tab tabId="login">Iniciar sesión</Tabs.Tab>
                    <Tabs.Tab tabId="register">Registrarse</Tabs.Tab>
                  </Tabs>
                </div>

                {/* Formulario */}
                <form onSubmit={onSubmit} className="mt-8 space-y-4">
                  {mode === 'register' && (
                    <>
                      <div>
                        <label className="mb-1 block text-sm text-neutral-300">Nombre</label>
                        <input
                          type="text"
                          value={name}
                          onChange={(e) => setName(e.target.value)}
                          placeholder="Tu nombre"
                          required
                          className="block w-full rounded-md border border-neutral-500/40 bg-transparent px-4 py-3 text-white placeholder-neutral-400 outline-none focus:ring-2 focus:ring-cyan-400"
                        />
                      </div>

                      <div>
                        <label className="mb-1 block text-sm text-neutral-300">Profesión</label>
                        <select
                          value={profession}
                          onChange={(e) => setProfession(e.target.value)}
                          required
                          className="block w-full rounded-md border border-neutral-500/40 bg-transparent px-4 py-3 text-white outline-none focus:ring-2 focus:ring-cyan-400"
                        >
                          <option value="" className="text-black">Seleccioná tu profesión</option>
                          <option value="medicina" className="text-black">Médica/o</option>
                          <option value="enfermeria" className="text-black">Enfermera/o</option>
                          <option value="kinesiologia" className="text-black">Kinesióloga/o</option>
                          <option value="nutricion" className="text-black">Nutricionista</option>
                          <option value="farmacia" className="text-black">Farmacéutica/o</option>
                          <option value="estudiante" className="text-black">Estudiante</option>
                          <option value="otro" className="text-black">Otro</option>
                        </select>
                      </div>
                    </>
                  )}

                  <div>
                    <label className="mb-1 block text-sm text-neutral-300">Email</label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@email.com"
                      required
                      className="block w-full rounded-md border border-neutral-500/40 bg-transparent px-4 py-3 text-white placeholder-neutral-400 outline-none focus:ring-2 focus:ring-cyan-400"
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-sm text-neutral-300">Contraseña</label>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      required
                      className="block w-full rounded-md border border-neutral-500/40 bg-transparent px-4 py-3 text-white placeholder-neutral-400 outline-none focus:ring-2 focus:ring-cyan-400"
                    />
                  </div>

                  <Button type="submit" className="w-full !bg-cyan-400 !text-black hover:!bg-cyan-300">
                    {mode === 'login' ? 'Iniciar sesión' : 'Crear cuenta'}
                  </Button>
                </form>
              </div>
            </div>
          </div>
        </Widget>
      </div>
    </>
  );
}



