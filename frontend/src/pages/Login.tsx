import { zodResolver } from "@hookform/resolvers/zod";
import { Activity, Database, LogIn, ShieldCheck, Sparkles } from "lucide-react";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";

import LanguageSelector from "../components/LanguageSelector";
import { useAuth } from "../context/AuthContext";

type LoginFormValues = { email: string; password: string; mfa_code?: string };

const demoCredentials = [
  ["auth.admin", "admin@prescripta.local", "Admin@12345"],
  ["auth.doctor", "medico@prescripta.local", "Medico@12345"],
  ["auth.nursing", "enfermagem@prescripta.local", "Enfermagem@12345"],
  ["auth.auditor", "auditor@prescripta.local", "Auditor@12345"],
] as const;

const loginSignals = [
  { icon: ShieldCheck, labelKey: "auth.signalSafety", detailKey: "auth.signalSafetyDetail" },
  { icon: Database, labelKey: "auth.signalEvidence", detailKey: "auth.signalEvidenceDetail" },
  { icon: Sparkles, labelKey: "auth.signalAI", detailKey: "auth.signalAIDetail" },
] as const;

export default function Login() {
  const { isAuthenticated, login } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const loginSchema = useMemo(() => z.object({
    email: z.string().min(5, t("auth.emailRequired")),
    password: z.string().min(1, t("auth.passwordRequired")),
    mfa_code: z.string().regex(/^\d{6}$/, t("auth.mfaFormat")).or(z.literal("")).optional(),
  }), [t]);
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
    setError,
    setValue,
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "admin@prescripta.local", password: "Admin@12345", mfa_code: "" },
  });

  if (isAuthenticated) return <Navigate replace to="/" />;

  async function submit(values: LoginFormValues) {
    try {
      await login(values.email, values.password, values.mfa_code);
      const target = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      navigate(target || "/", { replace: true });
    } catch {
      setError("root", { message: t("auth.invalid") });
    }
  }

  return (
    <main className="login-canvas min-h-screen px-4 py-6 text-ink sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-6xl justify-end"><LanguageSelector /></div>
      <div className="mx-auto grid min-h-[calc(100vh-6rem)] w-full max-w-6xl items-center gap-10 py-8 lg:grid-cols-[minmax(0,1.15fr)_minmax(24rem,.85fr)]">
        <section>
          <div className="inline-flex items-center gap-3 rounded-2xl border border-cyan-900/10 bg-white/75 p-2 pr-4 shadow-soft">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-ocean text-white"><Activity aria-hidden="true" className="h-6 w-6" /></span>
            <span className="text-lg font-black tracking-[-0.03em]">Prescripta</span>
          </div>
          <h1 className="mt-8 max-w-2xl text-4xl font-black tracking-[-0.055em] text-ink sm:text-5xl lg:text-6xl">{t("auth.title")}</h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-slate-600">{t("auth.description")}</p>
          <div className="mt-8 grid max-w-xl gap-3 sm:grid-cols-3">
            {loginSignals.map(({ icon: Icon, labelKey, detailKey }) => (
              <div className="rounded-2xl border border-cyan-950/10 bg-white/70 p-4" key={labelKey}>
                <Icon aria-hidden="true" className="h-5 w-5 text-ocean" />
                <p className="mt-3 text-xs font-black text-ink">{t(labelKey)}</p>
                <p className="mt-1 text-[0.6875rem] text-slate-500">{t(detailKey)}</p>
              </div>
            ))}
          </div>
          <p className="mt-6 max-w-xl rounded-2xl border border-amber-200 bg-amber-50/90 p-4 text-sm font-semibold leading-6 text-amber-950">{t("auth.demoNotice")}</p>
        </section>

        <section className="rounded-[1.75rem] border border-cyan-950/10 bg-white p-6 shadow-float sm:p-8">
          <h2 className="text-2xl font-black tracking-tight text-ink">{t("auth.signIn")}</h2>
          <form className="mt-6 grid gap-4" onSubmit={handleSubmit(submit)}>
            <label className="grid gap-1.5"><span className="label">{t("auth.email")}</span><input className="field" type="email" {...register("email")} />{errors.email ? <span className="field-error">{errors.email.message}</span> : null}</label>
            <label className="grid gap-1.5"><span className="label">{t("auth.mfa")}</span><input autoComplete="one-time-code" className="field" inputMode="numeric" maxLength={6} {...register("mfa_code")} />{errors.mfa_code ? <span className="field-error">{errors.mfa_code.message}</span> : null}</label>
            <label className="grid gap-1.5"><span className="label">{t("auth.password")}</span><input className="field" type="password" {...register("password")} />{errors.password ? <span className="field-error">{errors.password.message}</span> : null}</label>
            {errors.root ? <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm font-semibold text-danger">{errors.root.message}</p> : null}
            <button className="btn-primary" disabled={isSubmitting} title={t("auth.signIn")} type="submit"><LogIn aria-hidden="true" className="h-4 w-4" />{t("auth.signIn")}</button>
          </form>
          <div className="mt-7 grid gap-2 border-t border-slate-100 pt-5">
            <p className="text-xs font-black uppercase tracking-[0.12em] text-slate-500">{t("auth.demoCredentials")}</p>
            <p className="mb-1 text-xs leading-5 text-slate-500">{t("auth.profileHint")}</p>
            {demoCredentials.map(([labelKey, email, password]) => (
              <button className="rounded-xl border border-slate-200 px-3 py-2.5 text-left text-xs text-slate-600 transition hover:border-cyan-700 hover:bg-cyan-50/40 hover:text-ocean" key={email} onClick={() => { setValue("email", email); setValue("password", password); }} type="button"><span className="font-extrabold text-ink">{t(labelKey)}</span> · {email}</button>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
