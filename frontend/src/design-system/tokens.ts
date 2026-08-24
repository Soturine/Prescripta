export const designTokens = {
  color: {
    text: { strong: "#102033", default: "#334155", muted: "#64748b", inverse: "#ffffff" },
    surface: { canvas: "#f3f5f4", raised: "#ffffff", muted: "#edf2f1", clinical: "#e7f3f0", research: "#eef0f8" },
    border: { subtle: "#dce4e2", strong: "#aebdb9" },
    action: { primary: "#075f64", hover: "#064e52", subtle: "#dcefed" },
    focus: "#0891b2",
    status: { success: "#13795b", warning: "#9a5d06", danger: "#b42318", info: "#176b87" },
    severity: { critical: "#9f1239", high: "#b42318", moderate: "#9a5d06", low: "#13795b" },
    ai: { text: "#5935a8", surface: "#f2edff", border: "#cbbdf3" },
    chart: { primary: "#075f64", secondary: "#176b87", comparison: "#7c3aed", neutral: "#94a3b8", warning: "#c47a0a" },
  },
  spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, "2xl": 48 },
  radius: { control: 8, panel: 12, dialog: 16 },
  elevation: { raised: "0 1px 2px rgba(15, 23, 42, .06)", overlay: "0 18px 48px -24px rgba(15, 23, 42, .42)" },
  typography: { measure: "72ch", tabular: "tabular-nums" },
  motion: { fast: 120, normal: 180 },
  breakpoints: { mobile: 320, compact: 390, tablet: 768, desktop: 1024, wide: 1440 },
  control: { minimumTarget: 44 },
  zIndex: { base: 0, topbar: 30, overlay: 40, drawer: 50, dialog: 60 },
} as const;

export type DesignTokens = typeof designTokens;
