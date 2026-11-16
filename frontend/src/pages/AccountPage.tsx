import { useState, type FormEvent } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import { PageHeader, Status } from "../components";
import type { User } from "../types";

export function AccountPage() {
  const { user, refresh } = useAuth(); const [saved, setSaved] = useState(false); const [error, setError] = useState("");
  const submit = async (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); setSaved(false); const display_name = String(new FormData(event.currentTarget).get("displayName")); try { await api<User>("/api/account", { method: "PATCH", body: JSON.stringify({ display_name }) }); await refresh(); setSaved(true); } catch (e) { setError((e as Error).message); } };
  return <><PageHeader eyebrow="Profile and privacy" title="Account settings">Manage the identity shown in this workspace. Predictions, batches and conversations remain isolated to this account.</PageHeader><div className="grid gap-8 lg:grid-cols-[1fr_1fr]"><form className="panel p-6" onSubmit={submit}><h2 className="text-3xl">Profile</h2><label className="mt-5 block text-sm font-bold">Display name<input className="field mt-2" name="displayName" defaultValue={user?.display_name} minLength={2} maxLength={80} required /></label><label className="mt-5 block text-sm font-bold">Email address<input className="field mt-2 opacity-60" value={user?.email || ""} disabled /></label>{saved && <div className="mt-5"><Status type="success">Profile saved.</Status></div>}{error && <div className="mt-5"><Status type="error">{error}</Status></div>}<button className="button mt-6">Save changes</button></form><section className="border bg-ink p-6 text-ivory"><p className="eyebrow !text-ivory/50">Security posture</p><h2 className="mt-2 text-4xl">Your session is server managed.</h2><ul className="mt-6 space-y-3 text-sm leading-6 text-ivory/65"><li>• Passwords are hashed with Argon2id.</li><li>• The session token is held in an HttpOnly cookie.</li><li>• State-changing requests require a CSRF token.</li><li>• Ownership is derived from the session—not a browser-supplied user ID.</li><li>• Logging out clears account-specific browser state.</li></ul><p className="mt-8 border-t border-ivory/20 pt-5 text-xs text-ivory/40">Account created {user ? new Date(user.created_at).toLocaleString() : "—"}</p></section></div></>;
}

