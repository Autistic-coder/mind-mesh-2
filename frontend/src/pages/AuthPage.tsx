import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api";
import { useAuth } from "../auth";
import { Status } from "../components";

export function AuthPage({ mode }: { mode: "login" | "register" }) {
  const { user, login, register } = useAuth();
  const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const navigate = useNavigate(); const location = useLocation();
  if (user) return <Navigate to="/" replace />;
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); if (busy) return; setBusy(true); setError("");
    const data = new FormData(event.currentTarget);
    try {
      if (mode === "login") await login(String(data.get("email")), String(data.get("password")));
      else await register(String(data.get("email")), String(data.get("displayName")), String(data.get("password")));
      const destination = (location.state as { from?: string } | null)?.from || "/"; navigate(destination, { replace: true });
    } catch (caught) { setError(caught instanceof ApiError ? caught.message : "Unable to continue"); } finally { setBusy(false); }
  };
  const loginMode = mode === "login";
  return <main className="grid min-h-screen bg-ink text-ivory lg:grid-cols-[1.1fr_.9fr]">
    <section className="relative hidden overflow-hidden border-r border-ivory/20 p-12 lg:flex lg:flex-col lg:justify-between">
      <div className="absolute -right-32 top-16 h-80 w-80 rotate-12 border border-acid/40" aria-hidden="true" />
      <div className="eyebrow !text-acid">MindMesh 2 / Predictive maintenance</div>
      <div className="relative max-w-2xl"><h1 className="font-display text-7xl leading-[.86]">Read the machine.<br /><em className="text-acid">Before it stops.</em></h1><p className="mt-7 max-w-lg text-sm leading-7 text-ivory/60">A focused Random Forest decision-support system for industrial machine-failure risk. Evidence-led, private by account, and built for clear maintenance conversations.</p></div>
      <p className="text-xs text-ivory/40">AI4I 2020 · Model v1.0.0 · Six operating measurements</p>
    </section>
    <section className="flex items-center justify-center bg-ivory p-5 text-ink"><div className="w-full max-w-md border border-ink/25 bg-white/50 p-6 backdrop-blur md:p-9">
      <Link to="/" className="font-display text-2xl font-semibold">MindMesh <span className="text-moss">2</span></Link>
      <p className="eyebrow mt-12">{loginMode ? "Welcome back" : "Create workspace"}</p><h2 className="mt-2 font-display text-5xl font-semibold">{loginMode ? "Sign in" : "Register"}</h2>
      <form className="mt-8 space-y-5" onSubmit={submit}>
        {!loginMode && <label className="block text-sm font-semibold">Display name<input className="field mt-2" name="displayName" minLength={2} maxLength={80} autoComplete="name" required /></label>}
        <label className="block text-sm font-semibold">Email address<input className="field mt-2" name="email" type="email" autoComplete="email" required /></label>
        <label className="block text-sm font-semibold">Password<input className="field mt-2" name="password" type="password" minLength={loginMode ? 1 : 10} autoComplete={loginMode ? "current-password" : "new-password"} required />{!loginMode && <span className="mt-1 block text-xs font-normal text-ink/55">Use at least 10 characters.</span>}</label>
        {error && <Status type="error">{error}</Status>}
        <button className="button w-full" disabled={busy}>{busy ? "Please wait…" : loginMode ? "Sign in" : "Create account"}</button>
      </form>
      <p className="mt-6 text-center text-sm text-ink/60">{loginMode ? "New to MindMesh?" : "Already registered?"} <Link className="font-bold underline decoration-acid decoration-4" to={loginMode ? "/register" : "/login"}>{loginMode ? "Create an account" : "Sign in"}</Link></p>
    </div></section>
  </main>;
}

