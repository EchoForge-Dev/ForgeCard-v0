import { motion } from "framer-motion";
import { truncateMiddle } from "@/lib/format";

export default function ScanningView({ address }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="flex h-full flex-col items-center justify-center gap-8"
    >
      <div className="relative flex h-36 w-36 items-center justify-center">
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{ border: "1px solid var(--border-color)" }}
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 4, ease: "linear" }}
        />
        <motion.div
          className="absolute inset-4 rounded-full"
          style={{ border: "1px solid rgba(255,255,255,0.3)" }}
          animate={{ rotate: -360 }}
          transition={{ repeat: Infinity, duration: 2.5, ease: "linear" }}
        />
        <div
          className="absolute inset-10 rounded-full glass-panel-subtle"
          style={{ overflow: "hidden" }}
        >
          <div className="scan-line-overlay" />
        </div>
      </div>

      <div className="text-center">
        <h1
          className="text-xl font-semibold uppercase tracking-[0.2em]"
          style={{ color: "var(--text-primary)" }}
        >
          Verifying Identity...
        </h1>
        {address ? <p className="value-tech mt-3 text-center">{truncateMiddle(address)}</p> : null}
      </div>
    </motion.div>
  );
}
