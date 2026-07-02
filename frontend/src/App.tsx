import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import Audit from "./pages/Audit";
import Dashboard from "./pages/Dashboard";
import Medications from "./pages/Medications";
import PatientDetails from "./pages/PatientDetails";
import Patients from "./pages/Patients";
import PrescriptionCheck from "./pages/PrescriptionCheck";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="patients" element={<Patients />} />
        <Route path="patients/:patientId" element={<PatientDetails />} />
        <Route path="medications" element={<Medications />} />
        <Route path="prescription-check" element={<PrescriptionCheck />} />
        <Route path="audit" element={<Audit />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
