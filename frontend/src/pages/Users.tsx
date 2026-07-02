import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Save } from "lucide-react";
import type { FormEvent } from "react";
import { useState } from "react";

import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import {
  createUser,
  fetchUsers,
  updateUserRole,
  updateUserStatus,
} from "../services/api";
import type { UserCreatePayload, UserRole } from "../types/user";
import { formatDateTime, formatRole } from "../utils/formatters";

const roles: UserRole[] = ["admin", "medico", "enfermagem", "auditor"];

export default function Users() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<UserCreatePayload>({
    name: "",
    email: "",
    password: "",
    role: "medico",
    is_active: true,
  });
  const { data: users = [], isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: fetchUsers,
  });
  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: async () => {
      setForm({ name: "", email: "", password: "", role: "medico", is_active: true });
      await queryClient.invalidateQueries({ queryKey: ["users"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const statusMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      updateUserStatus(id, is_active),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["users"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const roleMutation = useMutation({
    mutationFn: ({ id, role }: { id: number; role: UserRole }) => updateUserRole(id, role),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["users"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await createMutation.mutateAsync(form);
  }

  return (
    <div className="grid gap-6">
      <header>
        <h1 className="text-3xl font-bold tracking-normal text-ink">Usuários</h1>
        <p className="mt-2 text-sm text-slate-600">Gestão administrativa de perfis e status.</p>
      </header>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-bold text-ink">Novo usuário</h2>
        <form className="mt-5 grid gap-4" onSubmit={handleCreate}>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="grid gap-1.5">
              <span className="label">Nome</span>
              <input
                className="field"
                onChange={(event) => setForm((value) => ({ ...value, name: event.target.value }))}
                required
                value={form.name}
              />
            </label>
            <label className="grid gap-1.5">
              <span className="label">E-mail</span>
              <input
                className="field"
                onChange={(event) => setForm((value) => ({ ...value, email: event.target.value }))}
                required
                type="email"
                value={form.email}
              />
            </label>
            <label className="grid gap-1.5">
              <span className="label">Senha</span>
              <input
                className="field"
                minLength={8}
                onChange={(event) =>
                  setForm((value) => ({ ...value, password: event.target.value }))
                }
                required
                type="password"
                value={form.password}
              />
            </label>
            <label className="grid gap-1.5">
              <span className="label">Perfil</span>
              <select
                className="field"
                onChange={(event) =>
                  setForm((value) => ({ ...value, role: event.target.value as UserRole }))
                }
                value={form.role}
              >
                {roles.map((role) => (
                  <option key={role} value={role}>
                    {formatRole(role)}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="inline-flex items-center gap-2 text-sm font-semibold text-slate-700">
            <input
              checked={form.is_active}
              onChange={(event) =>
                setForm((value) => ({ ...value, is_active: event.target.checked }))
              }
              type="checkbox"
            />
            Ativo
          </label>
          <button className="btn-primary w-fit" disabled={createMutation.isPending} type="submit">
            <Plus aria-hidden="true" className="h-4 w-4" />
            Criar usuário
          </button>
          {createMutation.isError ? (
            <p className="text-sm font-semibold text-danger">Não foi possível criar usuário.</p>
          ) : null}
        </form>
      </section>

      <section className="grid gap-3">
        <h2 className="text-lg font-bold text-ink">Usuários cadastrados</h2>
        {isLoading ? <LoadingState label="Carregando usuários" /> : null}
        {!isLoading && users.length === 0 ? <EmptyState title="Nenhum usuário cadastrado" /> : null}
        {!isLoading && users.length > 0 ? (
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[880px] text-left text-sm">
                <thead className="bg-slate-50 text-xs font-bold uppercase tracking-normal text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Nome</th>
                    <th className="px-4 py-3">E-mail</th>
                    <th className="px-4 py-3">Perfil</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Criado em</th>
                    <th className="px-4 py-3 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {users.map((user) => (
                    <tr key={user.id} className="text-slate-700">
                      <td className="px-4 py-3 font-semibold text-ink">{user.name}</td>
                      <td className="px-4 py-3">{user.email}</td>
                      <td className="px-4 py-3">
                        <select
                          className="field"
                          onChange={(event) =>
                            roleMutation.mutate({
                              id: user.id,
                              role: event.target.value as UserRole,
                            })
                          }
                          value={user.role}
                        >
                          {roles.map((role) => (
                            <option key={role} value={role}>
                              {formatRole(role)}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-3">{user.is_active ? "Ativo" : "Inativo"}</td>
                      <td className="px-4 py-3">{formatDateTime(user.created_at)}</td>
                      <td className="px-4 py-3 text-right">
                        <button
                          className="btn-secondary"
                          onClick={() =>
                            statusMutation.mutate({ id: user.id, is_active: !user.is_active })
                          }
                          title={user.is_active ? "Inativar usuário" : "Ativar usuário"}
                          type="button"
                        >
                          <Save aria-hidden="true" className="h-4 w-4" />
                          {user.is_active ? "Inativar" : "Ativar"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}
      </section>
    </div>
  );
}
