import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

export function Button({ children, className = "", ...props }: PropsWithChildren<ButtonHTMLAttributes<HTMLButtonElement>>) {
  return <button className={`rounded-lg bg-cyan-400 px-4 py-2 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50 ${className}`} {...props}>{children}</button>;
}

export function Card({ children, className = "" }: PropsWithChildren<{ className?: string }>) {
  return <section className={`rounded-xl border border-slate-700/70 bg-slate-900/70 p-5 shadow-xl shadow-slate-950/20 ${className}`}>{children}</section>;
}

export function Badge({ children, tone = "slate" }: PropsWithChildren<{ tone?: "slate" | "green" | "red" | "amber" | "cyan" }>) {
  const colours = { slate: "bg-slate-700 text-slate-200", green: "bg-emerald-500/15 text-emerald-300", red: "bg-rose-500/15 text-rose-300", amber: "bg-amber-500/15 text-amber-300", cyan: "bg-cyan-400/15 text-cyan-200" };
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-bold tracking-wide ${colours[tone]}`}>{children}</span>;
}

export function Notice({ children, kind = "error" }: PropsWithChildren<{ kind?: "error" | "success" | "info" }>) {
  const colours = { error: "border-rose-500/40 bg-rose-500/10 text-rose-100", success: "border-emerald-500/40 bg-emerald-500/10 text-emerald-100", info: "border-cyan-400/40 bg-cyan-400/10 text-cyan-100" };
  return <div role={kind === "error" ? "alert" : "status"} className={`rounded-lg border px-4 py-3 text-sm ${colours[kind]}`}>{children}</div>;
}

export const formatDate = (value: string) => new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
export const formatBytes = (bytes: number) => `${(bytes / 1024 / 1024).toFixed(bytes > 1024 * 1024 ? 1 : 2)} MB`;
