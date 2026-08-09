import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, FileText, ShieldCheck, Sparkles, UsersRound } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import ClinicalContextGraphCard from "../components/ClinicalContextGraphCard";
import ClinicalProfileCard from "../components/ClinicalProfileCard";
import FunctionalProfileCard from "../components/FunctionalProfileCard";
import LoadingState from "../components/LoadingState";
import PageHeader from "../components/PageHeader";
import PatientForm from "../components/PatientForm";
import QuickTriageForm from "../components/QuickTriageForm";
import Badge from "../components/ui/Badge";
import Modal from "../components/ui/Modal";
import StatusPanel from "../components/ui/StatusPanel";
import { useAuth } from "../context/AuthContext";
import {
  createPatientAccessGrant,
  fetchPatient,
  fetchPatientAccessGrants,
  fetchPatientCareTeam,
  fetchPatientClinicalContext,
  fetchPatientDocuments,
  fetchPatientFunctionalProfile,
  fetchPatientKnowledgeBundle,
  fetchPatientPsychologicalContext,
  fetchPatientTimeline,
  createPatientDocument,
  extractPatientDocument,
  reviewPatientDocumentExtraction,
  revokePatientAccessGrant,
  quickTriagePatient,
  updatePatientPsychologicalContext,
  updatePatientFunctionalProfile,
  updatePatient,
} from "../services/api";
import type { CareTeamMembership, PatientAccessGrant } from "../types/access";
import type {
  PatientFunctionalProfilePayload,
  PatientPayload,
  PatientPsychologicalContext,
  PatientPsychologicalContextPayload,
  QuickTriagePayload,
} from "../types/patient";
import type { Capability } from "../types/user";
import { formatStatus, humanizeTechnicalValue } from "../utils/formatters";

export default function PatientDetails() {
  const { can } = useAuth();
  const { t } = useTranslation();
  const canManagePatient = can("patient.write");
  const canReadPsychology = can("patient.sensitive_psychology.read");
  const canWritePsychology = can("psychology.context.write");
  const canManageAccess = can("access.manage");
  const queryClient = useQueryClient();
  const params = useParams();
  const patientId = Number(params.patientId);
  const [documentTitle, setDocumentTitle] = useState("Laudo ou observação clínica");
  const [documentText, setDocumentText] = useState("");
  const { data: patient, isLoading } = useQuery({
    queryKey: ["patients", patientId],
    queryFn: () => fetchPatient(patientId),
    enabled: Number.isFinite(patientId),
  });
  const { data: clinicalContext } = useQuery({
    queryKey: ["patients", patientId, "clinical-context"],
    queryFn: () => fetchPatientClinicalContext(patientId),
    enabled: Number.isFinite(patientId),
  });
  const { data: functionalProfile } = useQuery({
    queryKey: ["patients", patientId, "functional-profile"],
    queryFn: () => fetchPatientFunctionalProfile(patientId),
    enabled: Number.isFinite(patientId),
  });
  const { data: documents = [] } = useQuery({
    queryKey: ["patients", patientId, "documents"],
    queryFn: () => fetchPatientDocuments(patientId),
    enabled: Number.isFinite(patientId),
  });
  const { data: timeline = [] } = useQuery({
    queryKey: ["patients", patientId, "timeline"],
    queryFn: () => fetchPatientTimeline(patientId),
    enabled: Number.isFinite(patientId),
  });
  const { data: knowledgeBundle } = useQuery({
    queryKey: ["patients", patientId, "knowledge-bundle"],
    queryFn: () => fetchPatientKnowledgeBundle(patientId),
    enabled: Number.isFinite(patientId),
  });
  const psychologyQuery = useQuery({
    queryKey: ["patients", patientId, "psychological-context"],
    queryFn: () => fetchPatientPsychologicalContext(patientId),
    enabled: Number.isFinite(patientId) && canReadPsychology,
    retry: false,
  });
  const { data: accessGrants = [] } = useQuery({
    queryKey: ["patients", patientId, "access-grants"],
    queryFn: () => fetchPatientAccessGrants(patientId),
    enabled: Number.isFinite(patientId) && canManageAccess,
  });
  const { data: careTeam = [] } = useQuery({
    queryKey: ["patients", patientId, "care-team"],
    queryFn: () => fetchPatientCareTeam(patientId),
    enabled: Number.isFinite(patientId) && canManageAccess,
  });
  const updateMutation = useMutation({
    mutationFn: (payload: PatientPayload) => updatePatient(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patients"] });
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId] });
    },
  });
  const quickTriageMutation = useMutation({
    mutationFn: (payload: QuickTriagePayload) => quickTriagePatient(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patients"] });
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId] });
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId, "clinical-context"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const functionalProfileMutation = useMutation({
    mutationFn: (payload: PatientFunctionalProfilePayload) =>
      updatePatientFunctionalProfile(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId, "functional-profile"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const createDocumentMutation = useMutation({
    mutationFn: () =>
      createPatientDocument(patientId, {
        document_type: "clinical_note",
        title: documentTitle,
        summary: "Texto clínico cadastrado manualmente.",
        source_type: "manual_text",
        source_system: "prescripta",
        raw_text: documentText,
      }),
    onSuccess: async () => {
      setDocumentText("");
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId, "documents"] });
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId, "timeline"] });
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId, "knowledge-bundle"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const extractMutation = useMutation({
    mutationFn: (documentId: number) => extractPatientDocument(patientId, documentId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId, "documents"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const reviewExtractionMutation = useMutation({
    mutationFn: (payload: { extractionId: number; entities: Record<string, unknown> }) =>
      reviewPatientDocumentExtraction(patientId, payload.extractionId, {
        decision: "accept",
        accepted_entities: payload.entities,
        justification: "Revisão humana demonstrativa v0.8.3.",
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patients"] });
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId] });
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId, "documents"] });
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId, "timeline"] });
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId, "knowledge-bundle"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const psychologyMutation = useMutation({
    mutationFn: (payload: PatientPsychologicalContextPayload) =>
      updatePatientPsychologicalContext(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["patients", patientId, "psychological-context"],
      });
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const grantMutation = useMutation({
    mutationFn: (payload: {
      user_id: number;
      capability: string;
      purpose: string;
      reason: string;
    }) => createPatientAccessGrant(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["patients", patientId, "access-grants"],
      });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const revokeGrantMutation = useMutation({
    mutationFn: ({ grantId, reason }: { grantId: number; reason: string }) =>
      revokePatientAccessGrant(grantId, reason),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["patients", patientId, "access-grants"],
      });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });

  if (isLoading) {
    return <LoadingState label={t("patients.loading")} />;
  }

  if (!patient) {
    return (
      <div className="grid gap-4">
        <Link className="btn-secondary w-fit" to="/patients">
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          {t("patients.back")}
        </Link>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-semibold text-red-700">
          {t("patients.notFound")}
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      <PageHeader
        actions={
          <Link className="btn-secondary w-fit" to="/patients">
            <ArrowLeft aria-hidden="true" className="h-4 w-4" />
            {t("patients.backList")}
          </Link>
        }
        description={t("patients.workspaceDescription")}
        title={patient.name}
      />

      <nav aria-label={t("patients.sections")} className="overflow-x-auto rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
        <div className="flex min-w-max gap-1">
          {[
            ["#profile", t("patients.profile")],
            ["#documents", t("patients.documents")],
            ["#functional", t("patients.functional")],
            ["#psychology", t("patients.psychology")],
            ["#access", t("patients.access")],
            ["#activity", t("patients.activity")],
          ].map(([href, label]) => (
            <a className="rounded-xl px-3 py-2 text-sm font-bold text-slate-600 hover:bg-slate-100 hover:text-ink" href={href} key={href}>
              {label}
            </a>
          ))}
        </div>
      </nav>

      <section className="scroll-mt-28 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm" id="profile">
        {canManagePatient ? (
          <>
            <PatientForm
              key={patient.id}
              initialPatient={patient}
              onSubmit={async (payload) => {
                await updateMutation.mutateAsync(payload);
              }}
              submitLabel="Salvar paciente"
            />
            {updateMutation.isError ? (
              <p className="mt-3 text-sm font-semibold text-danger">Não foi possível salvar.</p>
            ) : null}
            {updateMutation.isSuccess ? (
              <p className="mt-3 text-sm font-semibold text-mint">Paciente atualizado.</p>
            ) : null}
          </>
        ) : (
          <dl className="grid gap-4 text-sm md:grid-cols-2">
            <div>
              <dt className="label">Idade</dt>
              <dd className="mt-1 font-semibold text-ink">{patient.age ?? "-"}</dd>
            </div>
            <div>
              <dt className="label">Peso</dt>
              <dd className="mt-1 font-semibold text-ink">{patient.weight_kg} kg</dd>
            </div>
            <div>
              <dt className="label">Alergias</dt>
              <dd className="mt-1 font-semibold text-ink">
                {patient.allergies.join(", ") || "-"}
              </dd>
            </div>
            <div>
              <dt className="label">Comorbidades</dt>
              <dd className="mt-1 font-semibold text-ink">
                {patient.comorbidities.join(", ") || "-"}
              </dd>
            </div>
            <div className="md:col-span-2">
              <dt className="label">Medicamentos contínuos</dt>
              <dd className="mt-1 font-semibold text-ink">
                {patient.current_medications.join(", ") || "-"}
              </dd>
            </div>
          </dl>
        )}
      </section>

      <ClinicalProfileCard patient={patient} />

      <section className="scroll-mt-28 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]" id="documents">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-cyan-50 text-ocean">
              <FileText aria-hidden="true" className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-ink">Histórico clínico e laudos</h2>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                Textos, PDFs pesquisáveis e observações entram como documento pendente até revisão.
                Imagem/OCR permanece como cadastro manual assistido nesta versão.
              </p>
            </div>
          </div>

          {canManagePatient ? (
            <div className="mt-4 grid gap-3">
              <label className="grid gap-1.5">
                <span className="label">Título</span>
                <input
                  className="field"
                  onChange={(event) => setDocumentTitle(event.target.value)}
                  value={documentTitle}
                />
              </label>
              <label className="grid gap-1.5">
                <span className="label">Texto do laudo/documento</span>
                <textarea
                  className="field min-h-32"
                  onChange={(event) => setDocumentText(event.target.value)}
                  placeholder="Cole aqui o texto pesquisável do laudo, exame, observação ou resumo externo."
                  value={documentText}
                />
              </label>
              <button
                className="btn-primary w-fit"
                disabled={!documentText.trim() || createDocumentMutation.isPending}
                onClick={() => createDocumentMutation.mutate()}
                type="button"
              >
                <FileText aria-hidden="true" className="h-4 w-4" />
                Anexar texto
              </button>
            </div>
          ) : null}

          {extractMutation.data ? (
            <div className="mt-4 rounded-lg border border-cyan-100 bg-cyan-50 p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-sm font-bold text-ink">Extração pendente de revisão</p>
                  <p className="mt-1 text-sm text-slate-700">
                    Provider: {extractMutation.data.provider} · confiança{" "}
                    {Math.round(extractMutation.data.confidence * 100)}%
                  </p>
                </div>
                <button
                  className="btn-primary"
                  disabled={reviewExtractionMutation.isPending}
                  onClick={() =>
                    reviewExtractionMutation.mutate({
                      extractionId: extractMutation.data.id,
                      entities: extractMutation.data.extracted_entities,
                    })
                  }
                  type="button"
                >
                  <CheckCircle2 aria-hidden="true" className="h-4 w-4" />
                  Aceitar itens
                </button>
              </div>
              <pre className="mt-3 max-h-56 overflow-auto rounded-lg bg-white p-3 text-xs text-slate-700">
                {JSON.stringify(extractMutation.data.extracted_entities, null, 2)}
              </pre>
            </div>
          ) : null}

          <div className="mt-5 grid gap-3">
            {documents.length ? (
              documents.map((document) => (
                <article className="rounded-lg border border-slate-100 bg-slate-50 p-4" key={document.id}>
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="font-bold text-ink">{document.title}</p>
                      <p className="mt-1 text-sm text-slate-600">
                        {humanizeTechnicalValue(document.document_type)} · {formatStatus(document.review_status)}
                      </p>
                    </div>
                    {canManagePatient ? (
                      <button
                        className="btn-secondary"
                        disabled={extractMutation.isPending}
                        onClick={() => extractMutation.mutate(document.id)}
                        type="button"
                      >
                        <Sparkles aria-hidden="true" className="h-4 w-4" />
                        Extrair dados
                      </button>
                    ) : null}
                  </div>
                  {Object.keys(document.extracted_entities ?? {}).length ? (
                    <div className="mt-3 rounded-lg border border-cyan-100 bg-white p-3 text-sm text-slate-700">
                      <pre className="max-h-44 overflow-auto whitespace-pre-wrap">
                        {JSON.stringify(document.extracted_entities, null, 2)}
                      </pre>
                    </div>
                  ) : null}
                </article>
              ))
            ) : (
              <p className="text-sm text-slate-600">Nenhum laudo/documento anexado.</p>
            )}
          </div>
        </div>

        <div className="grid content-start gap-4">
          <div className="scroll-mt-28 rounded-lg border border-slate-200 bg-white p-5 shadow-sm" id="activity">
            <div className="flex items-center gap-3">
              <CheckCircle2 aria-hidden="true" className="h-5 w-5 text-ocean" />
              <h2 className="text-lg font-bold text-ink">PatientKnowledgeBundle</h2>
            </div>
            <div className="mt-4 grid gap-2 text-sm text-slate-600">
              <p>Documentos revisados: {knowledgeBundle?.reviewed_documents.length ?? 0}</p>
              <p>Extrações revisadas: {knowledgeBundle?.reviewed_extractions.length ?? 0}</p>
              <p>Medicamentos históricos: {knowledgeBundle?.medication_history.length ?? 0}</p>
              <p>Dados faltantes: {knowledgeBundle?.missing_data.join(", ") || "-"}</p>
            </div>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-bold text-ink">Linha do tempo do paciente</h2>
            <ol className="mt-4 grid gap-3">
              {timeline.length ? (
                timeline.slice(0, 8).map((event, index) => (
                  <li className="flex gap-3" key={`${event.id ?? index}-${event.title}`}>
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-cyan-50 text-xs font-bold text-ocean">
                      {index + 1}
                    </span>
                    <div>
                      <p className="font-semibold text-ink">{String(event.title ?? "-")}</p>
                      <p className="mt-1 text-sm text-slate-600">{String(event.event_type ?? "")}</p>
                    </div>
                  </li>
                ))
              ) : (
                <li className="text-sm text-slate-600">Sem eventos longitudinais ainda.</li>
              )}
            </ol>
          </div>
        </div>
      </section>

      <div className="scroll-mt-28" id="functional">
        {functionalProfile ? (
          <FunctionalProfileCard
            canManage={canManagePatient}
            isSaving={functionalProfileMutation.isPending}
            onSubmit={async (payload) => {
              await functionalProfileMutation.mutateAsync(payload);
            }}
            profile={functionalProfile}
          />
        ) : null}
      </div>

      <PsychologySection
        canRead={canReadPsychology}
        canWrite={canWritePsychology}
        context={psychologyQuery.data}
        isError={psychologyQuery.isError}
        isLoading={psychologyQuery.isLoading}
        isSaving={psychologyMutation.isPending}
        onSave={async (payload) => psychologyMutation.mutateAsync(payload)}
        saveError={psychologyMutation.isError}
        saveSuccess={psychologyMutation.isSuccess}
      />

      <AccessSection
        canManage={canManageAccess}
        careTeam={careTeam}
        grants={accessGrants}
        isCreating={grantMutation.isPending}
        isRevoking={revokeGrantMutation.isPending}
        mutationError={grantMutation.isError || revokeGrantMutation.isError}
        onCreate={async (payload) => grantMutation.mutateAsync(payload)}
        onRevoke={async (grantId, reason) =>
          revokeGrantMutation.mutateAsync({ grantId, reason })
        }
      />

      {canManagePatient ? (
        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-bold text-ink">Triagem rápida</h2>
          <div className="mt-5">
            <QuickTriageForm
              onSubmit={async (payload) => {
                await quickTriageMutation.mutateAsync(payload);
              }}
            />
          </div>
          {quickTriageMutation.isSuccess ? (
            <p className="mt-3 text-sm font-semibold text-mint">Triagem atualizada.</p>
          ) : null}
        </section>
      ) : null}

      {clinicalContext ? <ClinicalContextGraphCard graph={clinicalContext} /> : null}
    </div>
  );
}

function PsychologySection({
  canRead,
  canWrite,
  context,
  isError,
  isLoading,
  isSaving,
  onSave,
  saveError,
  saveSuccess,
}: {
  canRead: boolean;
  canWrite: boolean;
  context?: PatientPsychologicalContext;
  isError: boolean;
  isLoading: boolean;
  isSaving: boolean;
  onSave: (payload: PatientPsychologicalContextPayload) => Promise<unknown>;
  saveError: boolean;
  saveSuccess: boolean;
}) {
  if (!canRead) {
    return (
      <div className="scroll-mt-28" id="psychology">
        <StatusPanel title="Segmento psicológico protegido" tone="info">
          Este perfil não possui a capacidade de leitura do contexto psicológico. Nenhum conteúdo sensível foi consultado.
        </StatusPanel>
      </div>
    );
  }

  return (
    <section className="scroll-mt-28 rounded-2xl border border-violet-200 bg-white p-5 shadow-sm" id="psychology">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck aria-hidden="true" className="h-5 w-5 text-violet-700" />
            <h2 className="text-lg font-extrabold text-ink">Contexto psicológico segmentado</h2>
          </div>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Acesso auditado por finalidade. Somente fatores minimizados de segurança medicamentosa seguem para o perfil clínico; notas confidenciais não seguem para IA ou relatórios.
          </p>
        </div>
        <Badge tone="ai">Conteúdo sensível</Badge>
      </div>

      {isLoading ? <div className="skeleton mt-5 h-28 rounded-xl" aria-label="Carregando contexto psicológico" /> : null}
      {!isLoading && isError && !canWrite ? (
        <p className="mt-5 text-sm text-slate-600">Não há contexto disponível para a finalidade de tratamento neste vínculo.</p>
      ) : null}
      {!isLoading && (context || canWrite) ? (
        <form
          className="mt-5 grid gap-4"
          key={context?.updated_at ?? "new-context"}
          onSubmit={async (event) => {
            event.preventDefault();
            const data = new FormData(event.currentTarget);
            await onSave({
              purpose: "treatment",
              medication_safety_factors: String(data.get("medication_safety_factors") ?? "")
                .split(",")
                .map((item) => item.trim())
                .filter(Boolean),
              confidential_notes: String(data.get("confidential_notes") ?? "").trim() || null,
              consent_status: String(data.get("consent_status")) as PatientPsychologicalContextPayload["consent_status"],
              policy_reference: String(data.get("policy_reference") ?? "").trim() || null,
            });
          }}
        >
          <label className="grid gap-1.5">
            <span className="label">Fatores de segurança medicamentosa</span>
            <input className="field" defaultValue={context?.medication_safety_factors.join(", ") ?? ""} disabled={!canWrite} name="medication_safety_factors" placeholder="Ex.: dificuldade de adesão, risco de sedação" />
            <span className="text-xs text-slate-500">Separe os fatores controlados por vírgula. Não inclua diagnóstico narrativo.</span>
          </label>
          <label className="grid gap-1.5">
            <span className="label">Notas confidenciais</span>
            <textarea className="field min-h-28" defaultValue={context?.confidential_notes ?? ""} disabled={!canWrite} name="confidential_notes" />
          </label>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="grid gap-1.5">
              <span className="label">Base de consentimento</span>
              <select className="field" defaultValue={context?.consent_status ?? "policy_required"} disabled={!canWrite} name="consent_status">
                <option value="recorded">Consentimento registrado</option>
                <option value="waived_by_policy">Dispensado por política</option>
                <option value="policy_required">Política exige registro</option>
              </select>
            </label>
            <label className="grid gap-1.5">
              <span className="label">Referência da política</span>
              <input className="field" defaultValue={context?.policy_reference ?? ""} disabled={!canWrite} name="policy_reference" />
            </label>
          </div>
          {canWrite ? (
            <button className="btn-primary w-fit" disabled={isSaving} type="submit">
              {isSaving ? "Salvando…" : "Salvar segmento protegido"}
            </button>
          ) : null}
          {saveError ? <p className="text-sm font-semibold text-danger" role="alert">Não foi possível salvar o contexto.</p> : null}
          {saveSuccess ? <p className="text-sm font-semibold text-mint" role="status">Contexto salvo e acesso auditado.</p> : null}
        </form>
      ) : null}
    </section>
  );
}

const GRANTABLE_CAPABILITIES: Capability[] = [
  "patient.read",
  "patient.write",
  "patient.sensitive_psychology.read",
  "psychology.context.write",
  "prescription.check",
];

function AccessSection({
  canManage,
  careTeam,
  grants,
  isCreating,
  isRevoking,
  mutationError,
  onCreate,
  onRevoke,
}: {
  canManage: boolean;
  careTeam: CareTeamMembership[];
  grants: PatientAccessGrant[];
  isCreating: boolean;
  isRevoking: boolean;
  mutationError: boolean;
  onCreate: (payload: { user_id: number; capability: string; purpose: string; reason: string }) => Promise<unknown>;
  onRevoke: (grantId: number, reason: string) => Promise<unknown>;
}) {
  const [revoking, setRevoking] = useState<PatientAccessGrant | null>(null);

  if (!canManage) {
    return (
      <div className="scroll-mt-28" id="access">
        <StatusPanel title="Vínculo assistencial aplicado" tone="success">
          Os dados exibidos neste workspace já estão limitados ao vínculo, à finalidade e às capacidades da sessão. A gestão dos grants é restrita aos responsáveis autorizados.
        </StatusPanel>
      </div>
    );
  }

  return (
    <section className="scroll-mt-28 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm" id="access">
      <div className="flex items-start gap-3">
        <UsersRound aria-hidden="true" className="mt-0.5 h-5 w-5 text-ocean" />
        <div>
          <h2 className="text-lg font-extrabold text-ink">Equipe, vínculo e grants</h2>
          <p className="mt-1 text-sm leading-6 text-slate-600">Conceda somente capacidades que o profissional já possui. Toda alteração registra motivo e auditoria.</p>
        </div>
      </div>

      <form
        className="mt-5 grid gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 md:grid-cols-2 xl:grid-cols-4"
        onSubmit={async (event) => {
          event.preventDefault();
          const form = event.currentTarget;
          const data = new FormData(form);
          await onCreate({
            user_id: Number(data.get("user_id")),
            capability: String(data.get("capability")),
            purpose: "treatment",
            reason: String(data.get("reason")),
          });
          form.reset();
        }}
      >
        <label className="grid gap-1.5">
          <span className="label">ID do profissional</span>
          <input className="field" min="1" name="user_id" required type="number" />
        </label>
        <label className="grid gap-1.5">
          <span className="label">Capacidade</span>
          <select className="field" name="capability">
            {GRANTABLE_CAPABILITIES.map((capability) => <option key={capability} value={capability}>{capability}</option>)}
          </select>
        </label>
        <label className="grid gap-1.5 md:col-span-2">
          <span className="label">Motivo do vínculo</span>
          <input className="field" minLength={8} name="reason" placeholder="Motivo assistencial auditável" required />
        </label>
        <button className="btn-primary w-fit" disabled={isCreating} type="submit">{isCreating ? "Concedendo…" : "Conceder acesso"}</button>
      </form>
      {mutationError ? <p className="mt-3 text-sm font-semibold text-danger" role="alert">A operação foi recusada. Confirme o profissional, a capacidade e o motivo.</p> : null}

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <div>
          <h3 className="text-sm font-extrabold text-ink">Grants individuais ({grants.length})</h3>
          <div className="mt-3 grid gap-2">
            {grants.length ? grants.map((grant) => (
              <article className="rounded-xl border border-slate-200 p-3" key={grant.id}>
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div><p className="font-bold text-ink">Profissional #{grant.user_id}</p><p className="mt-1 text-sm text-slate-600">{grant.capability} · {grant.purpose}</p></div>
                  <Badge tone={grant.revoked_at ? "neutral" : "success"}>{grant.revoked_at ? "Revogado" : "Ativo"}</Badge>
                </div>
                {grant.reason ? <p className="mt-2 text-sm text-slate-600">{grant.reason}</p> : null}
                {!grant.revoked_at ? <button className="btn-secondary mt-3" onClick={() => setRevoking(grant)} type="button">Revogar grant</button> : null}
              </article>
            )) : <p className="text-sm text-slate-600">Nenhum grant individual registrado.</p>}
          </div>
        </div>
        <div>
          <h3 className="text-sm font-extrabold text-ink">Equipe assistencial ({careTeam.length})</h3>
          <div className="mt-3 grid gap-2">
            {careTeam.length ? careTeam.map((member) => (
              <article className="rounded-xl border border-slate-200 p-3" key={member.id}>
                <div className="flex flex-wrap items-start justify-between gap-2"><p className="font-bold text-ink">Profissional #{member.user_id}</p><Badge tone={member.revoked_at ? "neutral" : "info"}>{member.revoked_at ? "Encerrado" : member.care_role}</Badge></div>
                <p className="mt-1 text-sm text-slate-600">{member.team_code} · {member.capabilities.join(", ")}</p>
              </article>
            )) : <p className="text-sm text-slate-600">Nenhum vínculo de equipe registrado.</p>}
          </div>
        </div>
      </div>

      <Modal onClose={() => setRevoking(null)} open={Boolean(revoking)} title="Revogar acesso ao paciente">
        <form
          className="grid gap-4"
          onSubmit={async (event) => {
            event.preventDefault();
            if (!revoking) return;
            const reason = String(new FormData(event.currentTarget).get("reason"));
            await onRevoke(revoking.id, reason);
            setRevoking(null);
          }}
        >
          <p className="text-sm leading-6 text-slate-600">A revogação é imediata e auditada. O histórico do grant será preservado.</p>
          <label className="grid gap-1.5"><span className="label">Motivo da revogação</span><textarea className="field min-h-24" minLength={8} name="reason" required /></label>
          <div className="flex flex-wrap justify-end gap-2"><button className="btn-secondary" onClick={() => setRevoking(null)} type="button">Cancelar</button><button className="btn-danger" disabled={isRevoking} type="submit">{isRevoking ? "Revogando…" : "Confirmar revogação"}</button></div>
        </form>
      </Modal>
    </section>
  );
}
