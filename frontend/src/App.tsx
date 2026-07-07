import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import AccessDenied from "./pages/AccessDenied";
import AISettings from "./pages/AISettings";
import Audit from "./pages/Audit";
import ClinicalImports from "./pages/ClinicalImports";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Medications from "./pages/Medications";
import PatientDetails from "./pages/PatientDetails";
import Patients from "./pages/Patients";
import PrescriptionCheck from "./pages/PrescriptionCheck";
import Users from "./pages/Users";

export default function App() {
  return (
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

          <Route element={<ProtectedRoute roles={["admin", "medico", "enfermagem", "auditor"]} />}>
            <Route path="clinical-imports" element={<ClinicalImports />} />
          </Route>

          <Route element={<ProtectedRoute roles={["admin", "auditor"]} />}>
            <Route path="audit" element={<Audit />} />
          </Route>

          <Route element={<ProtectedRoute roles={["admin", "medico", "enfermagem", "auditor"]} />}>
            <Route path="settings/ai" element={<AISettings />} />
          </Route>

          <Route element={<ProtectedRoute roles={["admin"]} />}>
            <Route path="users" element={<Users />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Route>
    </Routes>
  );
}
