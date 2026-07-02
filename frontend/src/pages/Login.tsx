import { zodResolver } from "@hookform/resolvers/zod";
import { LogIn, ShieldCheck } from "lucide-react";
import { useForm } from "react-hook-form";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";

import { useAuth } from "../context/AuthContext";

const loginSchema = z.object({
  email: z.string().min(5, "Informe o e-mail."),
  password: z.string().min(1, "Informe a senha."),
});

type LoginFormValues = z.infer<typeof loginSchema>;

const demoCredentials = [
  ["Admin", "admin@prescripta.local", "Admin@12345"],
  ["Médico", "medico@prescripta.local", "Medico@12345"],
  ["Enfermagem", "enfermagem@prescripta.local", "Enfermagem@12345"],
  ["Auditor", "auditor@prescripta.local", "Auditor@12345"],
];

export default function Login() {
  const { isAuthenticated, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
    setError,
    setValue,
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "admin@prescripta.local",
      password: "Admin@12345",
    },
  });

  if (isAuthenticated) {
    return <Navigate replace to="/" />;
  }

  async function submit(values: LoginFormValues) {
    try {
      await login(values.email, values.password);
      const target = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      navigate(target || "/", { replace: true });
    } catch {
      setError("root", { message: "E-mail ou senha inválidos, ou usuário inativo." });
    }
  }

  return (
    <main className="min-h-screen bg-[#f4f8fb] px-4 py-10 text-ink">
      <div className="mx-auto grid min-h-[calc(100vh-5rem)] w-full max-w-5xl items-center gap-8 lg:grid-cols-[1fr_420px]">
        <section>
          <div className="flex h-14 w-14 items-center justify-center rounded-lg bg-ocean text-white">
            <ShieldCheck aria-hidden="true" className="h-7 w-7" />
          </div>
          <h1 className="mt-6 text-4xl font-bold tracking-normal text-ink">Prescripta</h1>
          <p className="mt-4 max-w-xl text-base leading-7 text-slate-600">
            Acesso demonstrativo com perfis para validar autorização, auditoria e proteção de
            rotas no MVP educacional.
          </p>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-soft">
          <h2 className="text-xl font-bold text-ink">Entrar</h2>
          <form className="mt-5 grid gap-4" onSubmit={handleSubmit(submit)}>
            <label className="grid gap-1.5">
              <span className="label">E-mail</span>
              <input className="field" type="email" {...register("email")} />
              {errors.email ? (
                <span className="text-xs text-danger">{errors.email.message}</span>
              ) : null}
            </label>
            <label className="grid gap-1.5">
              <span className="label">Senha</span>
              <input className="field" type="password" {...register("password")} />
              {errors.password ? (
                <span className="text-xs text-danger">{errors.password.message}</span>
              ) : null}
            </label>

            {errors.root ? (
              <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-semibold text-danger">
                {errors.root.message}
              </p>
            ) : null}

            <button className="btn-primary" disabled={isSubmitting} title="Entrar" type="submit">
              <LogIn aria-hidden="true" className="h-4 w-4" />
              Entrar
            </button>
          </form>

          <div className="mt-6 grid gap-2 border-t border-slate-100 pt-4">
            <p className="text-xs font-bold uppercase tracking-normal text-slate-500">
              Credenciais demonstrativas
            </p>
            {demoCredentials.map(([label, email, password]) => (
              <button
                className="rounded-lg border border-slate-200 px-3 py-2 text-left text-xs text-slate-600 transition hover:border-ocean hover:text-ocean"
                key={email}
                onClick={() => {
                  setValue("email", email);
                  setValue("password", password);
                }}
                type="button"
              >
                <span className="font-bold text-ink">{label}</span> · {email}
              </button>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
