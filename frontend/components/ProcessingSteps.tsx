import { motion } from "framer-motion";
import { FileSearch, Zap, Brain, CheckCircle2 } from "lucide-react";

const STEPS = [
  { id: "parse", icon: FileSearch, label: "Parsing document", sub: "Extracting text & structure" },
  { id: "compress", icon: Zap, label: "Compressing tokens", sub: "Removing legal filler, extracting facts" },
  { id: "analyze", icon: Brain, label: "Analyzing with AI", sub: "RAG retrieval + LLM inference" },
  { id: "done", icon: CheckCircle2, label: "Done", sub: "Results ready" },
];

interface ProcessingStepsProps {
  currentStep: "parse" | "compress" | "analyze" | "done";
}

export default function ProcessingSteps({ currentStep }: ProcessingStepsProps) {
  const currentIdx = STEPS.findIndex((s) => s.id === currentStep);

  return (
    <div className="w-full py-8">
      <div className="flex flex-col gap-0">
        {STEPS.map((step, idx) => {
          const Icon = step.icon;
          const done = idx < currentIdx;
          const active = idx === currentIdx;
          const pending = idx > currentIdx;

          return (
            <div key={step.id} className="flex items-start gap-4">
              {/* Timeline line + icon */}
              <div className="flex flex-col items-center">
                <motion.div
                  className={`
                    w-9 h-9 rounded-xl flex items-center justify-center border shrink-0
                    ${done ? "bg-jade-400/15 border-jade-400/30" : ""}
                    ${active ? "bg-gold-400/12 border-gold-400/30" : ""}
                    ${pending ? "bg-white/[0.03] border-white/8" : ""}
                  `}
                  initial={false}
                  animate={active ? { scale: [1, 1.05, 1] } : { scale: 1 }}
                  transition={{ repeat: active ? Infinity : 0, duration: 2 }}
                >
                  {active ? (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    >
                      <Icon className="w-4 h-4 text-gold-400" />
                    </motion.div>
                  ) : (
                    <Icon
                      className={`w-4 h-4 ${done ? "text-jade-400" : "text-slate-600"}`}
                    />
                  )}
                </motion.div>

                {/* Connector line */}
                {idx < STEPS.length - 1 && (
                  <div className="w-px h-6 mt-1 relative overflow-hidden">
                    <div className="absolute inset-0 bg-white/8" />
                    {done && (
                      <motion.div
                        className="absolute inset-0 bg-jade-400/40"
                        initial={{ scaleY: 0, originY: 0 }}
                        animate={{ scaleY: 1 }}
                        transition={{ duration: 0.3 }}
                      />
                    )}
                  </div>
                )}
              </div>

              {/* Step text */}
              <div className="pt-1.5 pb-5">
                <motion.p
                  className={`text-sm font-medium leading-none ${
                    done ? "text-jade-400" : active ? "text-white" : "text-slate-600"
                  }`}
                  animate={active ? { opacity: [0.7, 1, 0.7] } : { opacity: 1 }}
                  transition={{ repeat: active ? Infinity : 0, duration: 1.5 }}
                >
                  {step.label}
                </motion.p>
                <p className={`text-xs mt-1 ${active ? "text-slate-400" : "text-slate-600"}`}>
                  {step.sub}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
