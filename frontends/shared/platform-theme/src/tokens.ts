export const colors = {
  bg: '#f0f4f8',
  white: '#ffffff',
  brandDark: '#0b2b5c',
  brandMid: '#0f3b7a',
  brandBlue: '#1248a0',
  accent: '#3b82f6',
  accentHover: '#2563eb',
  accentSoft: '#60a5fa',
  accentLight: '#93c5fd',
  textPrimary: '#1e293b',
  textSecondary: '#64748b',
  textMuted: '#94a3b8',
  textBody: '#334155',
  textCode: '#475569',
  borderLight: '#eef2f6',
  border: '#e2e8f0',
  borderHover: '#cbd5e1',
  borderAccent: '#bfdbfe',
  borderTable: '#e8edf3',
  rowHover: '#f8fafc',
  rowBorder: '#f1f5f9',
  iconBtnBg: '#f1f5f9',
  iconBtnHover: '#e2e8f0',
  sidebarText: 'rgba(255,255,255,0.7)',
  sidebarTextMuted: 'rgba(255,255,255,0.4)',
  sidebarHover: 'rgba(255,255,255,0.08)',
  sidebarActive: 'rgba(255,255,255,0.12)',
  sidebarBorder: 'rgba(255,255,255,0.08)',
  successBg: '#ecfdf5',
  successText: '#059669',
  warningBg: '#fff7ed',
  warningText: '#d97706',
  errorBg: '#fef2f2',
  errorText: '#dc2626',
  infoBg: '#eff6ff',
  dangerBg: '#fef2f2',
  dangerBorder: '#fecaca',
  dangerHoverBg: '#fee2e2',
  overlay: 'rgba(0, 0, 0, 0.03)',
} as const

export const spacing = {
  sidebarWidth: 240,
  topbarHeight: 64,
  contentPaddingX: 32,
  contentPaddingY: 28,
  cardPadding: 24,
  pageTitleMb: 24,
  toolbarMb: 20,
  sectionHeaderMb: 16,
  paginationMt: 20,
} as const

export const radius = {
  card: 14,
  btn: 8,
  tag: 12,
  pageBtn: 8,
  input: 8,
  modal: 12,
  resultCard: 12,
} as const

export const shadows = {
  sidebar: '2px 0 12px rgba(11, 43, 92, 0.15)',
  card: '0 1px 4px rgba(0,0,0,0.04)',
  header: '0 1px 3px rgba(0,0,0,0.03)',
  searchFocus: '0 0 0 3px rgba(59,130,246,0.1)',
  resultCardHover: '0 4px 12px rgba(59,130,246,0.06)',
} as const

export const typography = {
  fontFamily:
    '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif',
  fontMono: '"SF Mono", "Fira Code", monospace',
  pageTitleSize: 24,
  pageTitleWeight: 700,
  sectionTitleSize: 17,
  sectionTitleWeight: 600,
  cardTitleSize: 16,
  cardTitleWeight: 600,
  bodySize: 14,
  smallSize: 13,
  captionSize: 12,
  tinySize: 11,
} as const

export const nav = {
  sectionPadding: '16px 20px 6px',
  sectionFontSize: 11,
  sectionLetterSpacing: 1.5,
  itemGap: 12,
  itemPaddingY: 11,
  itemPaddingX: 20,
  itemFontSize: 14,
  subItemPaddingLeft: 55,
  subItemPaddingY: 9,
  subItemFontSize: 13,
  arrowSize: 11,
  dotSize: 4,
  iconWidth: 20,
  iconFontSize: 15,
  tagFutureFontSize: 10,
} as const

export const breadcrumb = {
  fontSize: 14,
  gap: 16,
} as const

export const cardGrid = {
  gap: 20,
  minWidth: 360,
} as const

export const pageBtn = {
  size: 34,
} as const
