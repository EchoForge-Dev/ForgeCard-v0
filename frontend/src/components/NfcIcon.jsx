export default function NfcIcon({ size = 72 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" aria-hidden="true">
      <rect
        x="6"
        y="14"
        width="36"
        height="36"
        rx="4"
        stroke="currentColor"
        strokeWidth="2"
        opacity="0.9"
      />
      <circle cx="24" cy="32" r="4" fill="currentColor" opacity="0.9" />
      <path
        d="M46 20a17 17 0 0 1 0 24"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.55"
      />
      <path
        d="M53 13a27 27 0 0 1 0 38"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.3"
      />
    </svg>
  );
}
