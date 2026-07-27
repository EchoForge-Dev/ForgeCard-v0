"use client";

import { AnimatePresence } from "framer-motion";
import StatusDot from "./StatusDot";
import IdleView from "./IdleView";
import ScanningView from "./ScanningView";
import ResultView from "./ResultView";
import ErrorView from "./ErrorView";
import { RESULT_AUTO_RETURN_MS, ERROR_AUTO_RETURN_MS } from "@/lib/constants";

const STATUS_BY_KIND = {
  idle: { variant: "inactive", label: "Standby" },
  scanning: { variant: "success", label: "Verifying" },
  result: { variant: "success", label: "Verified" },
  error: { variant: "warning", label: "Error" },
};

export default function KioskFrame({ viewState }) {
  const status = STATUS_BY_KIND[viewState.kind] ?? STATUS_BY_KIND.idle;

  return (
    <div
      className="relative flex h-screen w-screen flex-col overflow-hidden"
      style={{ background: "var(--bg-primary)" }}
    >
      <header className="flex h-12 shrink-0 items-center justify-between px-6">
        <div className="flex items-baseline gap-2">
          <span
            className="text-tech font-bold"
            style={{ color: "var(--text-primary)" }}
          >
            FORGECARD
          </span>
        </div>
        <div className="flex items-center gap-2">
          <StatusDot variant={status.variant} />
          <span className="label-tech">{status.label}</span>
        </div>
      </header>

      <main className="relative flex-1 px-8">
        <AnimatePresence mode="wait">
          {viewState.kind === "scanning" ? (
            <ScanningView key="scanning" address={viewState.address} />
          ) : viewState.kind === "result" ? (
            <ResultView key="result" profile={viewState.profile} autoReturnMs={RESULT_AUTO_RETURN_MS} />
          ) : viewState.kind === "error" ? (
            <ErrorView
              key="error"
              address={viewState.address}
              status={viewState.status}
              autoReturnMs={ERROR_AUTO_RETURN_MS}
            />
          ) : (
            <IdleView key="idle" />
          )}
        </AnimatePresence>
      </main>

      <footer className="flex h-8 shrink-0 items-center justify-center">
        <span className="text-tech" style={{ color: "var(--text-secondary)", opacity: 0.5 }}>
          All for Simple · 一切为简
        </span>
      </footer>
    </div>
  );
}
