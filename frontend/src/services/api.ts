import axios from "axios";

import type { AuditRecord, DashboardSummary } from "../types/audit";
import type { Medication, MedicationPayload } from "../types/medication";
import type { Patient, PatientPayload } from "../types/patient";
import type {
  PrescriptionCheckPayload,
  PrescriptionCheckResult,
} from "../types/prescription";

const baseURL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export const api = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});

export async function fetchDashboard() {
  const response = await api.get<DashboardSummary>("/dashboard");
  return response.data;
}

export async function fetchPatients() {
  const response = await api.get<Patient[]>("/patients");
  return response.data;
}

export async function fetchPatient(id: number) {
  const response = await api.get<Patient>(`/patients/${id}`);
  return response.data;
}

export async function createPatient(payload: PatientPayload) {
  const response = await api.post<Patient>("/patients", payload);
  return response.data;
}

export async function updatePatient(id: number, payload: PatientPayload) {
  const response = await api.put<Patient>(`/patients/${id}`, payload);
  return response.data;
}

export async function fetchMedications() {
  const response = await api.get<Medication[]>("/medications");
  return response.data;
}

export async function createMedication(payload: MedicationPayload) {
  const response = await api.post<Medication>("/medications", payload);
  return response.data;
}

export async function updateMedication(id: number, payload: MedicationPayload) {
  const response = await api.put<Medication>(`/medications/${id}`, payload);
  return response.data;
}

export async function checkPrescription(payload: PrescriptionCheckPayload) {
  const response = await api.post<PrescriptionCheckResult>("/prescriptions/check", payload);
  return response.data;
}

export async function fetchAudit() {
  const response = await api.get<AuditRecord[]>("/audit");
  return response.data;
}
