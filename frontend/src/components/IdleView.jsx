import { motion } from "framer-motion";
import CornerMarkers from "./CornerMarkers";
import NfcIcon from "./NfcIcon";

export default function IdleView() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="flex h-full flex-col items-center justify-center gap-8"
    >
      <motion.div
        animate={{ y: [0, -8, 0] }}
        transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
        className="relative flex h-36 w-36 items-center justify-center rounded-full glass-panel-strong"
        style={{ color: "var(--text-primary)" }}
      >
        <motion.div
          className="absolute inset-0 rounded-full"
          animate={{
            boxShadow: [
              "0 0 20px rgba(255,255,255,0.15), inset 0 0 20px rgba(255,255,255,0.05)",
              "0 0 40px rgba(255,255,255,0.3), inset 0 0 30px rgba(255,255,255,0.08)",
              "0 0 20px rgba(255,255,255,0.15), inset 0 0 20px rgba(255,255,255,0.05)",
            ],
          }}
          transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
        />
        <NfcIcon size={56} />
      </motion.div>

      <div className="relative px-10 py-6 text-center">
        <h1
          className="text-2xl font-bold uppercase tracking-[0.2em]"
          style={{ color: "var(--text-primary)" }}
        >
          Tap Card to Begin
        </h1>
        <p className="mt-3 text-[11px] uppercase tracking-[0.15em]" style={{ color: "var(--text-secondary)" }}>
          Place your Echo ID card near the reader
        </p>
      </div>
    </motion.div>
  );
}
