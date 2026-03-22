import { motion } from "framer-motion";
import { CalendarDays } from "lucide-react";

interface TimelineEvent {
  date: string;
  event: string;
}

interface TimelineCardProps {
  timeline: TimelineEvent[];
}

export default function TimelineCard({ timeline }: TimelineCardProps) {
  if (!timeline?.length) return null;

  return (
    <div className="glass rounded-2xl p-6 border border-white/6">
      <div className="flex items-center gap-2.5 mb-5">
        <div className="w-8 h-8 rounded-xl bg-violet-400/10 flex items-center justify-center">
          <CalendarDays className="w-4 h-4 text-violet-400" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-white">Timeline</h3>
          <p className="text-xs text-slate-500">Important dates and implementation schedule</p>
        </div>
      </div>

      <div className="relative pl-4">
        {/* Vertical line */}
        <div className="absolute left-0 top-2 bottom-2 w-px bg-white/8" />

        <div className="flex flex-col gap-4">
          {timeline.map((item, i) => (
            <motion.div
              key={i}
              className="relative"
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.09 }}
            >
              {/* Dot on the line */}
              <div className="absolute -left-[17px] top-1.5 w-2 h-2 rounded-full bg-violet-400/60 border border-violet-400/30" />

              <p className="text-xs font-medium text-violet-300 mb-1 font-mono">{item.date}</p>
              <p className="text-sm text-slate-300 leading-relaxed break-words overflow-wrap-anywhere">{item.event}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
