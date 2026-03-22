import { motion } from "framer-motion";
import { Lightbulb, ShieldAlert } from "lucide-react";

interface SummaryCardProps {
  summary: string;
  simplifiedExplanation: string;
  penaltiesAndCompliance: string;
  documentType: string;
}

export default function SummaryCard({
  summary,
  simplifiedExplanation,
  penaltiesAndCompliance,
  documentType,
}: SummaryCardProps) {
  return (
    <div className="flex flex-col gap-4">
      {/* Main summary */}
      <motion.div
        className="glass rounded-2xl p-6 border border-gold-400/12 glow-gold"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs px-2.5 py-1 rounded-full bg-gold-400/10 text-gold-400 border border-gold-400/20 font-medium">
            {documentType || "Legal Document"}
          </span>
          <span className="text-xs text-slate-500">· Summary</span>
        </div>
        <p className="text-sm sm:text-base text-white/90 leading-relaxed font-display break-words overflow-wrap-anywhere">{summary}</p>
      </motion.div>

      {/* Simplified for citizens */}
      {simplifiedExplanation && (
        <motion.div
          className="glass rounded-2xl p-6 border border-white/6"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-7 h-7 rounded-xl bg-amber-400/10 flex items-center justify-center">
              <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <p className="text-xs font-medium text-amber-400">We simplified this for you</p>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed break-words overflow-wrap-anywhere">{simplifiedExplanation}</p>
        </motion.div>
      )}

      {/* Penalties */}
      {penaltiesAndCompliance && (
        <motion.div
          className="glass rounded-2xl p-5 border border-scarlet-400/10"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-7 h-7 rounded-xl bg-scarlet-400/10 flex items-center justify-center">
              <ShieldAlert className="w-3.5 h-3.5 text-scarlet-400" />
            </div>
            <p className="text-xs font-medium text-scarlet-400">Penalties & Compliance</p>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed break-words overflow-wrap-anywhere">{penaltiesAndCompliance}</p>
        </motion.div>
      )}
    </div>
  );
}
