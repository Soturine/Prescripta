import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, FileText, Sparkles } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import ClinicalContextGraphCard from "../components/ClinicalContextGraphCard";
import ClinicalProfileCard from "../components/ClinicalProfileCard";
import FunctionalProfileCard from "../components/FunctionalProfileCard";
import LoadingState from "../components/LoadingState";
import PatientForm from "../components/PatientForm";
import QuickTriageForm from "../components/QuickTriageForm";
import { useAuth } from "../context/AuthContext";
import {
  fetchPatient,
  fetchPatientClinicalContext,
  fetchPatientDocuments,
  fetchPatientFunctionalProfile,
  fetchPatientKnowledgeBundle,
  fetchPatientTimeline,
  createPatientDocument,
  extractPatientDocument,
  reviewPatientDocumentExtraction,
  quickTriagePatient,
  updatePatientFunctionalProfile,
  updatePatient,
} from "../services/api";
import type {
  PatientFunctionalProfilePayload,
  PatientPayload,
  QuickTriagePayload,
} from "../types/patient";

export default function PatientDetails() {
  const { canAccess } = useAuth();
  const canManagePatient = canAccess(["admin", "medico"]);
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

  if (isLoading) {
    return <LoadingState label="Carregando paciente" />;
  }

  if (!patient) {
    return (
      <div className="grid gap-4">
        <Link className="btn-secondary w-fit" to="/patients">
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          Voltar
        </Link>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-semibold text-red-700">
          Paciente não encontrado.
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-normal text-ink">{patient.name}</h1>
          <p className="mt-1 text-sm text-slate-500">Cadastro de paciente</p>
        </div>
        <Link className="btn-secondary w-fit" to="/patients">
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          Voltar
        </Link>
      </header>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
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

      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
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
                        {document.document_type} · {document.review_status}
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
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
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
