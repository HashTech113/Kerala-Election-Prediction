export function asPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function asSeatPercent(seats: number, total: number): string {
  if (total <= 0) return "0.0%";
  return `${((seats / total) * 100).toFixed(1)}%`;
}
