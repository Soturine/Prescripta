import { lazy, Suspense } from "react";
import { useTranslation } from "react-i18next";
import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import LoadingState from "./components/LoadingState";
import ProtectedRoute from "./components/ProtectedRoute";

const AccessDenied = lazy(() => import("./pages/AccessDenied"));
const AISettings = lazy(() => import("./pages/AISettings"));
const Audit = lazy(() => import("./pages/Audit"));
const ClinicalImports = lazy(() => import("./pages/ClinicalImports"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Evidence = lazy(() => import("./pages/Evidence"));
const Help = lazy(() => import("./pages/Help"));
const Login = lazy(() => import("./pages/Login"));
const Medications = lazy(() => import("./pages/Medications"));
const PatientDetails = lazy(() => import("./pages/PatientDetails"));
const Patients = lazy(() => import("./pages/Patients"));
const Pharmacy = lazy(() => import("./pages/Pharmacy"));
const PrescriptionCheck = lazy(() => import("./pages/PrescriptionCheck"));
const Protocols = lazy(() => import("./pages/Protocols"));
const Reports = lazy(() => import("./pages/Reports"));
const Research = lazy(() => import("./pages/Research"));
const Users = lazy(() => import("./pages/Users"));

export default function App() {
  const { t } = useTranslation();
  return (
    <Suspense fallback={<LoadingState label={t("common.loadingScreen")} />}>
      <Routes>
        <Route path="login" element={<Login />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route element={<ProtectedRoute capabilities={["dashboard.view"]} />}>
              <Route index element={<Dashboard />} />
            </Route>
            <Route path="access-denied" element={<AccessDenied />} />
            <Route path="help" element={<Help />} />

            <Route element={<ProtectedRoute capabilities={["patient.read"]} />}>
              <Route path="patients" element={<Patients />} />
              <Route path="patients/:patientId" element={<PatientDetails />} />
            </Route>
            <Route element={<ProtectedRoute capabilities={["medication.read"]} />}>
              <Route path="medications" element={<Medications />} />
            </Route>
            <Route element={<ProtectedRoute capabilities={["pharmacy.intervention.read", "pharmacy.intervention.write", "pharmacy.intervention.decide"]} requireAnyCapability />}>
              <Route path="pharmacy" element={<Pharmacy />} />
            </Route>
            <Route element={<ProtectedRoute capabilities={["prescription.check"]} />}>
              <Route path="prescription-check" element={<PrescriptionCheck />} />
            </Route>

            <Route element={<ProtectedRoute capabilities={["reconciliation.review"]} />}>
              <Route path="clinical-imports" element={<ClinicalImports />} />
            </Route>
            <Route element={<ProtectedRoute capabilities={["report.read"]} />}>
              <Route path="protocols" element={<Protocols />} />
              <Route path="reports" element={<Reports />} />
            </Route>
            <Route element={<ProtectedRoute capabilities={["evidence.read"]} />}>
              <Route path="evidence" element={<Evidence />} />
            </Route>
            <Route element={<ProtectedRoute capabilities={["research.study.read"]} />}>
              <Route path="research" element={<Research />} />
            </Route>

            <Route element={<ProtectedRoute capabilities={["audit.read"]} />}>
              <Route path="audit" element={<Audit />} />
            </Route>

            <Route element={<ProtectedRoute capabilities={["ai.status.view"]} />}>
              <Route path="settings/ai" element={<AISettings />} />
            </Route>

            <Route element={<ProtectedRoute capabilities={["user.manage"]} />}>
              <Route path="users" element={<Users />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Route>
      </Routes>
    </Suspense>
  );
}
