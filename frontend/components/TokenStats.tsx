import { motion } from "framer-motion";
import { Zap } from "lucide-react";

interface TokenStatsProps {
  originalTokens: number;
  compressedTokens: number;
  tokensSaved: number;
  fromCache?: boolean;
}

export default function TokenStats({ originalTokens, compressedTokens, tokensSaved, fromCache }: TokenStatsProps) {
  const savingPercent = originalTokens > 0
    ? Math.round((tokensSaved / originalTokens) * 100)
    : 0;

  const fillPercent = Math.max(5, 100 - savingPercent);

  return (
    <div className="glass rounded-2xl p-5 border border-white/6">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-lg bg-gold-400/10 flex items-center justify-center">
          <Zap className="w-3.5 h-3.5 text-gold-400" />
        </div>
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Token Efficiency</span>
        {fromCache && (
          <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-jade-400/10 text-jade-400 border border-jade-400/20">
            cached
          </span>
        )}
      </div>

      {/* Progress bar */}
      <div className="w-full h-2 rounded-full bg-white/5 overflow-hidden mb-4">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-gold-400 to-gold-600"
          initial={{ width: "100%" }}
          animate={{ width: `${fillPercent}%` }}
          transition={{ duration: 1.2, ease: "easeOut" }}
        />
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        <div>
          <p className="text-lg font-semibold text-white font-mono">
            {originalTokens.toLocaleString()}
          </p>
          <p className="text-xs text-slate-500 mt-0.5">Original</p>
        </div>
        <div>
          <p className="text-lg font-semibold text-jade-400 font-mono">
            {tokensSaved.toLocaleString()}
          </p>
          <p className="text-xs text-slate-500 mt-0.5">Saved</p>
        </div>
        <div>
          <motion.p
            className="text-lg font-semibold text-gold-400 font-mono"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
          >
            {savingPercent}%
          </motion.p>
          <p className="text-xs text-slate-500 mt-0.5">Reduction</p>
        </div>
      </div>
    </div>
  );
}
