import medicinesUrl from "../../assets/third-party/health-icons/medicines.svg";
import researchUrl from "../../assets/third-party/health-icons/research.svg";

const icons = { medicines: medicinesUrl, research: researchUrl } as const;

export default function ClinicalPictogram({ kind }: { kind: keyof typeof icons }) {
  return <img alt="" aria-hidden="true" className="h-7 w-7 shrink-0 opacity-75" src={icons[kind]} />;
}
