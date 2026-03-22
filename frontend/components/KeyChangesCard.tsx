import { motion } from "framer-motion";
import { GitPullRequestArrow } from "lucide-react";

interface KeyChange {
  title: string;
  description: string;
  impact_level: "high" | "medium" | "low";
}

interface KeyChangesCardProps {
  changes: KeyChange[];
}

const impactConfig = {
  high: { label: "High Impact", cls: "badge-high" },
  medium: { label: "Medium", cls: "badge-medium" },
  low: { label: "Low", cls: "badge-low" },
};

export default function KeyChangesCard({ changes }: KeyChangesCardProps) {
  if (!changes?.length) return null;

  return (
    <div className="glass rounded-2xl p-6 border border-white/6">
      <div className="flex items-center gap-2.5 mb-5">
        <div className="w-8 h-8 rounded-xl bg-gold-400/10 flex items-center justify-center">
          <GitPullRequestArrow className="w-4 h-4 text-gold-400" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-white">Key Changes</h3>
          <p className="text-xs text-slate-500">What actually changed in this law</p>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {changes.map((change, i) => {
          const impact = impactConfig[change.impact_level] || impactConfig.medium;
          return (
            <motion.div
              key={i}
              className="p-4 rounded-xl bg-white/[0.03] border border-white/5 glass-hover"
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.08 }}
            >
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm font-medium text-white/90 leading-snug break-words overflow-wrap-anywhere">{change.title}</p>
                <span className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${impact.cls}`}>
                  {impact.label}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed break-words overflow-wrap-anywhere">{change.description}</p>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
