type Props = {
  size?: number;
  className?: string;
};

/** Cyan slash at 60° from horizontal — no background circle. */
export default function BrandLogo({ size = 36, className = "" }: Props) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <line
        x1="6"
        y1="26.93"
        x2="26"
        y2="3.36"
        stroke="#55e0ff"
        strokeWidth="3.5"
        strokeLinecap="round"
      />
    </svg>
  );
}
