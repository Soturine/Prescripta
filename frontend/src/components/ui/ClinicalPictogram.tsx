import medicinesUrl from "../../assets/third-party/health-icons/medicines.svg";
import researchUrl from "../../assets/third-party/health-icons/research.svg";

const icons = { medicines: medicinesUrl, research: researchUrl } as const;

export default function ClinicalPictogram({ kind }: { kind: keyof typeof icons }) {
  return (
    <span
      aria-hidden="true"
      className="inline-block h-7 w-7 shrink-0 bg-current"
      style={{
        maskImage: `url(${icons[kind]})`,
        maskPosition: "center",
        maskRepeat: "no-repeat",
        maskSize: "contain",
        WebkitMaskImage: `url(${icons[kind]})`,
        WebkitMaskPosition: "center",
        WebkitMaskRepeat: "no-repeat",
        WebkitMaskSize: "contain",
      }}
    />
  );
}
