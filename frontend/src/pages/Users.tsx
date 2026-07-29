import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound, Plus, Save, Search, ShieldCheck, UserCog } from "lucide-react";
import type { FormEvent, ReactNode } from "react";
import { useMemo, useState } from "react";

import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import PageHeader from "../components/PageHeader";
import Badge from "../components/ui/Badge";
import Modal from "../components/ui/Modal";
import StatusPanel from "../components/ui/StatusPanel";
import { CAPABILITY_LABELS, PROFESSIONAL_TEMPLATES } from "../config/professionalProfiles";
import { createUser, fetchUsers, updateUserClinicalProfile, updateUserRole, updateUserStatus } from "../services/api";
import type { Capability, User, UserCreatePayload, UserRole } from "../types/user";
import { formatDateTime, formatRole } from "../utils/formatters";

const roles = Object.keys(PROFESSIONAL_TEMPLATES) as UserRole[];

function initialUser(role: UserRole = "medico"): UserCreatePayload {
  const template = PROFESSIONAL_TEMPLATES[role];
  return {
    name: "",
    email: "",
    password: "",
    role,
    profession: template.profession,
    capabilities: [...template.capabilities],
    is_active: true,
    specialty_code: role === "medico" ? "general_practice" : null,
    specialty_codes: role === "medico" ? ["general_practice"] : [],
    credential_type: null,
    credential_code_demo: null,
    credential_region: null,
    crm_demo: null,
    crm_uf: null,
    rqe_demo: null,
    institutional_policy: {},
    sensitive_data_segments: role === "psicologo" ? ["psychology"] : [],
    institution_id: "demo",
  };
}

export default function Users() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<UserCreatePayload>(() => initialUser());
  const [createOpen, setCreateOpen] = useState(false);
  const [profileUser, setProfileUser] = useState<User | null>(null);
  const [profileCapabilities, setProfileCapabilities] = useState<Capability[]>([]);
  const [specialties, setSpecialties] = useState("");
  const [search, setSearch] = useState("");
  const { data: users = [], isLoading, error, refetch } = useQuery({ queryKey: ["users"], queryFn: fetchUsers });

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["users"] });
    await queryClient.invalidateQueries({ queryKey: ["audit"] });
  };
  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: async () => { setCreateOpen(false); setForm(initialUser()); await refresh(); },
  });
  const statusMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) => updateUserStatus(id, is_active),
    onSuccess: refresh,
  });
  const profileMutation = useMutation({
    mutationFn: async ({ user, capabilities, specialty_codes }: { user: User; capabilities: Capability[]; specialty_codes: string[] }) => updateUserClinicalProfile(user.id, { capabilities, specialty_codes, specialty_code: specialty_codes[0] ?? null }),
    onSuccess: async () => { setProfileUser(null); await refresh(); },
  });
  const roleMutation = useMutation({
    mutationFn: async ({ user, role }: { user: User; role: UserRole }) => {
      await updateUserRole(user.id, role);
      const template = PROFESSIONAL_TEMPLATES[role];
      return updateUserClinicalProfile(user.id, {
        profession: template.profession,
        capabilities: template.capabilities,
        specialty_code: role === "medico" ? "general_practice" : null,
        specialty_codes: role === "medico" ? ["general_practice"] : [],
        sensitive_data_segments: role === "psicologo" ? ["psychology"] : [],
      });
    },
    onSuccess: refresh,
  });

  const filteredUsers = useMemo(() => {
    const term = search.trim().toLocaleLowerCase("pt-BR");
    return users.filter((user) => !term || `${user.name} ${user.email} ${formatRole(user.role)}`.toLocaleLowerCase("pt-BR").includes(term));
  }, [search, users]);
  const isMedicalProfile = profileUser?.role === "medico";

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await createMutation.mutateAsync(form);
  }

  function changeFormRole(role: UserRole) {
    const defaults = initialUser(role);
    setForm((value) => ({ ...value, ...defaults, name: value.name, email: value.email, password: value.password, is_active: value.is_active }));
  }

  function openProfile(user: User) {
    setProfileUser(user);
    setProfileCapabilities([...user.capabilities]);
    setSpecialties(user.specialty_codes.join(", "));
    profileMutation.reset();
  }

  function toggleCapability(capability: Capability) {
    setProfileCapabilities((value) => value.includes(capability) ? value.filter((item) => item !== capability) : [...value, capability]);
  }

  async function changeRole(user: User, role: UserRole) {
    if (role === user.role) return;
    const confirmed = window.confirm(`Alterar ${user.name} para ${formatRole(role)}? As capacidades serão substituídas pelo template de menor privilégio.`);
    if (confirmed) await roleMutation.mutateAsync({ user, role });
  }

  return (
    <div className="grid gap-6 lg:gap-8">
      <PageHeader title="Acessos e perfis" description="Profissão, especialidade e capacidades são dimensões separadas. Administração não recebe acesso clínico automaticamente." actions={<button className="btn-primary" onClick={() => setCreateOpen(true)} type="button"><Plus aria-hidden="true" className="h-4 w-4" />Novo usuário</button>} />

      <StatusPanel title="Menor privilégio ativo" tone="info">Mudanças de papel aplicam um template seguro; capacidades podem ser reduzidas individualmente. A autorização por paciente continua exigindo vínculo, grant ou break-glass.</StatusPanel>

      <section className="surface-card p-4 sm:p-5">
        <label className="grid gap-1.5">
          <span className="label">Buscar usuário</span>
          <span className="relative max-w-xl"><Search aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><input className="field pl-10" onChange={(event) => setSearch(event.target.value)} placeholder="Nome, e-mail ou perfil" type="search" value={search} /></span>
        </label>
      </section>

      {isLoading ? <LoadingState label="Carregando perfis" /> : null}
      {error ? <StatusPanel actions={<button className="btn-secondary" onClick={() => void refetch()} type="button">Tentar novamente</button>} title="Falha ao carregar usuários" tone="danger" /> : null}
      {!isLoading && !error && filteredUsers.length === 0 ? <EmptyState title="Nenhum usuário encontrado" /> : null}

      {!isLoading && !error && filteredUsers.length ? (
        <div className="grid gap-3">
          {filteredUsers.map((user) => (
            <article className="surface-card p-4 sm:p-5" key={user.id}>
              <div className="grid gap-4 lg:grid-cols-[minmax(14rem,1fr)_minmax(14rem,.8fr)_minmax(13rem,.7fr)_auto] lg:items-center">
                <div className="flex items-start gap-3">
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-700"><UserCog aria-hidden="true" className="h-5 w-5" /></span>
                  <div className="min-w-0"><h2 className="truncate font-extrabold text-ink">{user.name}</h2><p className="truncate text-xs text-slate-500">{user.email}</p><div className="mt-2 flex flex-wrap gap-2"><Badge tone={user.is_active ? "success" : "neutral"}>{user.is_active ? "Ativo" : "Inativo"}</Badge><Badge>{user.capabilities.length} capacidades</Badge></div></div>
                </div>
                <label className="grid gap-1.5"><span className="label">Papel global</span><select className="field" disabled={roleMutation.isPending} onChange={(event) => void changeRole(user, event.target.value as UserRole)} value={user.role}>{roles.map((role) => <option key={role} value={role}>{formatRole(role)}</option>)}</select></label>
                <div><p className="label">Perfil profissional</p><p className="mt-1 text-sm font-bold text-slate-700">{PROFESSIONAL_TEMPLATES[user.role].description}</p><p className="mt-1 text-xs text-slate-500">Criado {formatDateTime(user.created_at)}</p></div>
                <div className="flex flex-wrap gap-2 lg:justify-end"><button className="btn-secondary" onClick={() => openProfile(user)} type="button"><KeyRound aria-hidden="true" className="h-4 w-4" />Capacidades</button><button className="btn-secondary" disabled={statusMutation.isPending} onClick={() => statusMutation.mutate({ id: user.id, is_active: !user.is_active })} type="button"><Save aria-hidden="true" className="h-4 w-4" />{user.is_active ? "Inativar" : "Ativar"}</button></div>
              </div>
            </article>
          ))}
        </div>
      ) : null}

      <Modal description="Somente dados fictícios. O template pode ser reduzido antes da criação." onClose={() => setCreateOpen(false)} open={createOpen} title="Novo usuário">
        <form className="grid gap-5" onSubmit={handleCreate}>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Nome"><input className="field" onChange={(event) => setForm((value) => ({ ...value, name: event.target.value }))} required value={form.name} /></Field>
            <Field label="E-mail"><input className="field" onChange={(event) => setForm((value) => ({ ...value, email: event.target.value }))} required type="email" value={form.email} /></Field>
            <Field label="Senha inicial"><input className="field" minLength={8} onChange={(event) => setForm((value) => ({ ...value, password: event.target.value }))} required type="password" value={form.password} /></Field>
            <Field label="Papel global"><select className="field" onChange={(event) => changeFormRole(event.target.value as UserRole)} value={form.role}>{roles.map((role) => <option key={role} value={role}>{formatRole(role)}</option>)}</select></Field>
            <Field label="Credencial demo"><input className="field" onChange={(event) => setForm((value) => ({ ...value, credential_code_demo: event.target.value || null }))} placeholder="Nunca use credencial real" value={form.credential_code_demo ?? ""} /></Field>
            <Field label="Região"><input className="field" maxLength={20} onChange={(event) => setForm((value) => ({ ...value, credential_region: event.target.value.toUpperCase() || null }))} value={form.credential_region ?? ""} /></Field>
          </div>
          <div className="subtle-panel p-4"><p className="text-sm font-extrabold text-ink">Template: {form.capabilities?.length ?? 0} capacidades</p><p className="mt-1 text-xs leading-5 text-slate-600">{PROFESSIONAL_TEMPLATES[form.role].description}</p></div>
          {createMutation.isError ? <p className="field-error" role="alert">Não foi possível criar. Revise o perfil e o e-mail.</p> : null}
          <button className="btn-primary justify-self-end" disabled={createMutation.isPending} type="submit"><Plus aria-hidden="true" className="h-4 w-4" />{createMutation.isPending ? "Criando…" : "Criar usuário"}</button>
        </form>
      </Modal>

      <Modal description="Selecione somente o necessário. O backend rejeita capacidades fora do template profissional." onClose={() => setProfileUser(null)} open={Boolean(profileUser)} title={`Capacidades de ${profileUser?.name ?? "usuário"}`}>
        {profileUser ? (
          <div>
            <div className="grid gap-2 sm:grid-cols-2">
              {PROFESSIONAL_TEMPLATES[profileUser.role].capabilities.map((capability) => (
                <label className="flex min-h-12 items-start gap-3 rounded-xl border border-slate-200 p-3 text-sm" key={capability}><input checked={profileCapabilities.includes(capability)} className="mt-0.5 h-4 w-4 accent-ocean" onChange={() => toggleCapability(capability)} type="checkbox" /><span><span className="block font-bold text-ink">{CAPABILITY_LABELS[capability]}</span><span className="mt-0.5 block text-xs text-slate-500">{capability}</span></span></label>
              ))}
            </div>
            {isMedicalProfile ? <div className="mt-4"><Field label="Especialidades (códigos separados por vírgula)"><input className="field" onChange={(event) => setSpecialties(event.target.value)} value={specialties} /></Field></div> : null}
            {profileMutation.isError ? <p className="field-error mt-3" role="alert">O backend recusou a combinação de profissão, especialidade ou capacidade.</p> : null}
            <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end"><button className="btn-secondary" onClick={() => setProfileUser(null)} type="button">Cancelar</button><button className="btn-primary" disabled={profileMutation.isPending} onClick={() => profileMutation.mutate({ user: profileUser, capabilities: profileCapabilities, specialty_codes: specialties.split(",").map((item) => item.trim()).filter(Boolean) })} type="button"><ShieldCheck aria-hidden="true" className="h-4 w-4" />Salvar menor privilégio</button></div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="grid gap-1.5"><span className="label">{label}</span>{children}</label>;
}
