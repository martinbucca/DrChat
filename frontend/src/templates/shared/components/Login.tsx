// src/pages/Login.tsx
import { useEffect, useState } from 'react';
import { Button, Widget, Tabs } from '@neo4j-ndl/react';
import { useNavigate } from 'react-router-dom';
import Header from './Header';
import DrChatLogo from '../assets/dr_chat_logo.png';
import axios from 'axios';

type FeedbackMessage = {
  type: 'success' | 'error';
  message: string;
};

export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<'login' | 'register'>('login');

  const [email, setEmail] = useState('');
  const [name, setName] = useState('');          // solo registro
  const [password, setPassword] = useState('');  // requerido en ambos
  const [profession, setProfession] = useState(''); // solo registro
  const [feedback, setFeedback] = useState<FeedbackMessage | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const user = localStorage.getItem('user');
    if (user) navigate('/', { replace: true });
  }, [navigate]);

  useEffect(() => {
    setFeedback(null);
  }, [mode]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    console.log("Starting login/register process");
    console.log("Mode:", mode);
    console.log("Email:", email);

    if (!email.trim() || !password.trim()) return;
    if (mode === 'register' && (!name.trim() || !profession.trim())) return;

    setFeedback(null);
    setIsSubmitting(true);

    try {
      const base = (import.meta as any).env.VITE_USER_SERVICE_URL || 'http://localhost:8004';
      console.log("Environment VITE_USER_SERVICE_URL:", (import.meta as any).env.VITE_USER_SERVICE_URL);
      console.log("Final API Base URL:", base);
      
      if (mode === 'register') {
        const url = `${base}/api/register`;
        console.log("Registering new user at URL:", url);
        const payload = {
          name,
          email,
          password,
          profesion: profession,
        };
        console.log("Register payload:", payload);
        
        const res = await axios.post(url, payload);
        console.log("Registration successful:", res.data);
        localStorage.setItem('user', JSON.stringify(res.data));
        setFeedback({ type: 'success', message: 'Usuario registrado' });
        setTimeout(() => {
          navigate('/', { replace: true });
        }, 1000);
        return;
      }

      const url = `${base}/api/login`;
      console.log("Logging in user at URL:", url);
      const payload = { email, password };
      console.log("Login payload:", { email, password: "***" });
      
      const res = await axios.post(url, payload);
      console.log("Login successful:", res.data);
      localStorage.setItem('user', JSON.stringify(res.data));

      console.log("Redirecting to home...");
      navigate('/', { replace: true });
    } catch (err) {
      console.error('Auth error:', err);
      console.error('Error details:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status,
        url: err.config?.url
      });
      if (axios.isAxiosError(err)) {
        const status = err.response?.status;
        const detail = err.response?.data as { detail?: string } | undefined;

        if (mode === 'register' && status === 400) {
          setFeedback({ type: 'error', message: 'El correo ya se encuentra registrado.' });
          return;
        }

        if (mode === 'login' && status === 401) {
          setFeedback({ type: 'error', message: 'Contraseña incorrecta.' });
          return;
        }

        if (typeof detail?.detail === 'string' && detail.detail.trim().length > 0) {
          setFeedback({ type: 'error', message: detail.detail });
          return;
        }
      }

      setFeedback({ type: 'error', message: 'No pudimos completar la autenticación. Intenta nuevamente.' });
    } finally {
      setIsSubmitting(false);
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
                <h2 className="mt-8 text-3xl font-semibold">DrChat: de documentos a respuestas</h2>
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
                  {feedback && (
                    <div
                      className={`flex items-center gap-3 rounded-2xl px-4 py-3 shadow-md border ${
                        feedback.type === 'success'
                          ? 'n-bg-palette-primary-bg-weak border-[rgb(var(--theme-palette-primary-border))] text-neutral-900'
                          : 'n-bg-palette-danger-bg-weak border-[rgb(var(--theme-palette-danger-border))] text-neutral-900'
                      }`}
                    >
                      <span className="font-medium">{feedback.message}</span>
                    </div>
                  )}

                  {mode === 'register' && (
                    <>
                      <div>
                        <label className="mb-1 block text-sm text-neutral-300">Nombre</label>
                        <input
                          type="text"
                          value={name}
                          onChange={(e) => {
                            setName(e.target.value);
                            setFeedback(null);
                          }}
                          placeholder="Tu nombre"
                          required
                          className="block w-full rounded-md border border-neutral-500/40 bg-transparent px-4 py-3 text-white placeholder-neutral-400 outline-none focus:ring-2 focus:ring-cyan-400"
                        />
                      </div>

                      <div>
                        <label className="mb-1 block text-sm text-neutral-300">Profesión</label>
                        <select
                          value={profession}
                          onChange={(e) => {
                            setProfession(e.target.value);
                            setFeedback(null);
                          }}
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
                      onChange={(e) => {
                        setEmail(e.target.value);
                        setFeedback(null);
                      }}
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
                      onChange={(e) => {
                        setPassword(e.target.value);
                        setFeedback(null);
                      }}
                      placeholder="••••••••"
                      required
                      className="block w-full rounded-md border border-neutral-500/40 bg-transparent px-4 py-3 text-white placeholder-neutral-400 outline-none focus:ring-2 focus:ring-cyan-400"
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full !bg-cyan-400 !text-black hover:!bg-cyan-300"
                    isDisabled={isSubmitting}
                  >
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
