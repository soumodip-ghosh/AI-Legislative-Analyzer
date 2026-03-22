import { motion } from "framer-motion";
import { Users } from "lucide-react";

interface AffectedEntity {
  entity: string;
  how: string;
}

interface AffectedEntitiesCardProps {
  entities: AffectedEntity[];
}

// Color wheel for entity tags — cycles through a set of muted palettes
const ENTITY_COLORS = [
  "bg-violet-400/10 text-violet-300 border-violet-400/20",
  "bg-sky-400/10 text-sky-300 border-sky-400/20",
  "bg-amber-400/10 text-amber-300 border-amber-400/20",
  "bg-rose-400/10 text-rose-300 border-rose-400/20",
  "bg-teal-400/10 text-teal-300 border-teal-400/20",
];

export default function AffectedEntitiesCard({ entities }: AffectedEntitiesCardProps) {
  if (!entities?.length) return null;

  return (
    <div className="glass rounded-2xl p-6 border border-white/6">
      <div className="flex items-center gap-2.5 mb-5">
        <div className="w-8 h-8 rounded-xl bg-sky-400/10 flex items-center justify-center">
          <Users className="w-4 h-4 text-sky-400" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-white">Who Is Affected</h3>
          <p className="text-xs text-slate-500">People and organisations this law touches</p>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {entities.map((e, i) => (
          <motion.div
              key={i}
              className="flex items-start gap-3 p-3.5 rounded-xl bg-white/[0.025] border border-white/5"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.07 }}
            >
              <span
                className={`text-xs px-2.5 py-1 rounded-lg border font-medium shrink-0 max-w-[40%]`}
              >
                {e.entity}
              </span>

              <p className="text-xs text-slate-400 leading-relaxed flex-1 break-words">
                {e.how}
              </p>
            </motion.div>
        ))}
      </div>
    </div>
  );
}
