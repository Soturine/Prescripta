import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import LoadingState from "./components/LoadingState";
import ProtectedRoute from "./components/ProtectedRoute";

const AccessDenied = lazy(() => import("./pages/AccessDenied"));
const AISettings = lazy(() => import("./pages/AISettings"));
const Audit = lazy(() => import("./pages/Audit"));
const ClinicalImports = lazy(() => import("./pages/ClinicalImports"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Login = lazy(() => import("./pages/Login"));
const Medications = lazy(() => import("./pages/Medications"));
const PatientDetails = lazy(() => import("./pages/PatientDetails"));
const Patients = lazy(() => import("./pages/Patients"));
const PrescriptionCheck = lazy(() => import("./pages/PrescriptionCheck"));
const Reports = lazy(() => import("./pages/Reports"));
const Users = lazy(() => import("./pages/Users"));

export default function App() {
  return (
    <Suspense fallback={<LoadingState label="Carregando tela" />}>
      <Routes>
        <Route path="login" element={<Login />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="access-denied" element={<AccessDenied />} />

            <Route element={<ProtectedRoute roles={["admin", "medico", "enfermagem"]} />}>
              <Route path="patients" element={<Patients />} />
              <Route path="patients/:patientId" element={<PatientDetails />} />
              <Route path="medications" element={<Medications />} />
              <Route path="prescription-check" element={<PrescriptionCheck />} />
            </Route>

            <Route
              element={<ProtectedRoute roles={["admin", "medico", "enfermagem", "auditor"]} />}
            >
              <Route path="clinical-imports" element={<ClinicalImports />} />
              <Route path="reports" element={<Reports />} />
            </Route>

            <Route element={<ProtectedRoute roles={["admin", "auditor"]} />}>
              <Route path="audit" element={<Audit />} />
            </Route>

            <Route
              element={<ProtectedRoute roles={["admin", "medico", "enfermagem", "auditor"]} />}
            >
              <Route path="settings/ai" element={<AISettings />} />
            </Route>

            <Route element={<ProtectedRoute roles={["admin"]} />}>
              <Route path="users" element={<Users />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Route>
      </Routes>
    </Suspense>
  );
}
