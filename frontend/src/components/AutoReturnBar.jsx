import { motion } from "framer-motion";

/** Progress bar that drains over `durationMs`, signalling the auto-return to idle. */
export default function AutoReturnBar({ durationMs }) {
  return (
    <div
      style={{
        height: 2,
        background: "var(--border-color)",
        borderRadius: 1,
        overflow: "hidden",
      }}
    >
      <motion.div
        style={{ height: "100%", background: "var(--text-primary)", borderRadius: 1 }}
        initial={{ width: "100%" }}
        animate={{ width: "0%" }}
        transition={{ duration: durationMs / 1000, ease: "linear" }}
      />
    </div>
  );
}
