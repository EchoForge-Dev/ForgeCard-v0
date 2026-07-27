import { motion } from "framer-motion";

const COLORS = {
  success: "#4EDE80",
  warning: "#EAB308",
  inactive: "#808080",
};

/** Breathing status dot. `variant` is "success" | "warning" | "inactive". */
export default function StatusDot({ variant = "inactive" }) {
  const color = COLORS[variant] ?? COLORS.inactive;

  if (variant === "inactive") {
    return (
      <div
        style={{ width: 6, height: 6, borderRadius: "50%", background: color, flexShrink: 0 }}
      />
    );
  }

  if (variant === "warning") {
    return (
      <motion.div
        animate={{ opacity: [1, 0.3, 1] }}
        transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
        style={{ width: 6, height: 6, borderRadius: "50%", background: color, flexShrink: 0 }}
      />
    );
  }

  return (
    <motion.div
      animate={{ scale: [1, 1.3, 1], opacity: [0.7, 1, 0.7] }}
      transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
      style={{ width: 6, height: 6, borderRadius: "50%", background: color, flexShrink: 0 }}
    />
  );
}
