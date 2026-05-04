export function formatRupees(value: number | undefined | null): string {
  const amount = value ?? 0;
  return `Rs. ${amount.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}
