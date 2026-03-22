import { motion } from "framer-motion";
import { IndianRupee } from "lucide-react";

interface FinancialImpact {
  description: string;
  figures: string[];
  who_pays: string;
  who_benefits: string;
}

interface FinancialImpactCardProps {
  impact: FinancialImpact;
}

export default function FinancialImpactCard({ impact }: FinancialImpactCardProps) {
  if (!impact?.description) return null;

  return (
    <div className="glass rounded-2xl p-6 border border-white/6">
      <div className="flex items-center gap-2.5 mb-5">
        <div className="w-8 h-8 rounded-xl bg-jade-400/10 flex items-center justify-center">
          <IndianRupee className="w-4 h-4 text-jade-400" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-white">Financial Impact</h3>
          <p className="text-xs text-slate-500">Money, penalties, and economic effects</p>
        </div>
      </div>

      <p className="text-sm text-slate-300 leading-relaxed mb-4 break-words overflow-wrap-anywhere">{impact.description}</p>

      {/* Key figures */}
      {impact.figures?.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {impact.figures.map((fig, i) => (
            <motion.span
              key={i}
              className="text-xs px-2.5 py-1 rounded-lg bg-jade-400/8 border border-jade-400/20 text-jade-300 font-mono"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05 }}
            >
              {fig}
            </motion.span>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        {impact.who_pays && (
          <div className="p-3 rounded-xl bg-scarlet-400/5 border border-scarlet-400/15">
            <p className="text-xs text-scarlet-400 font-medium mb-1">Who Pays</p>
            <p className="text-xs text-slate-400 leading-relaxed break-words overflow-wrap-anywhere">{impact.who_pays}</p>
          </div>
        )}
        {impact.who_benefits && (
          <div className="p-3 rounded-xl bg-jade-400/5 border border-jade-400/15">
            <p className="text-xs text-jade-400 font-medium mb-1">Who Benefits</p>
            <p className="text-xs text-slate-400 leading-relaxed break-words overflow-wrap-anywhere">{impact.who_benefits}</p>
          </div>
        )}
      </div>
    </div>
  );
}
