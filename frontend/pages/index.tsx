import Head from "next/head";
import { useState, useRef } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { Scale, AlertTriangle, RefreshCw } from "lucide-react";

import UploadZone from "../components/UploadZone";
import ProcessingSteps from "../components/ProcessingSteps";
import SummaryCard from "../components/SummaryCard";
import KeyChangesCard from "../components/KeyChangesCard";
import AffectedEntitiesCard from "../components/AffectedEntitiesCard";
import FinancialImpactCard from "../components/FinancialImpactCard";
import TimelineCard from "../components/TimelineCard";
import TokenStats from "../components/TokenStats";
import ChatCard from "../components/ChatCard";

type Step = "parse" | "compress" | "analyze" | "done";

interface AnalysisResult {
  summary: string;
  key_changes: any[];
  affected_entities: any[];
  financial_impact: any;
  timeline: any[];
  simplified_explanation: string;
  penalties_and_compliance: string;
  document_type: string;
  tokens_saved: number;
  original_tokens: number;
  compressed_tokens: number;
  is_legal: boolean;
  from_cache: boolean;
  doc_hash: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

// Fake step progression so the UI feels alive during a single long API call
function useStepProgress(active: boolean) {
  const [step, setStep] = useState<Step>("parse");
  const timerRef = useRef<NodeJS.Timeout[]>([]);

  const start = () => {
    setStep("parse");
    timerRef.current.push(setTimeout(() => setStep("compress"), 1800));
    timerRef.current.push(setTimeout(() => setStep("analyze"), 4000));
  };

  const finish = () => {
    setStep("done");
  };

  const reset = () => {
    timerRef.current.forEach(clearTimeout);
    timerRef.current = [];
    setStep("parse");
  };

  return { step, start, finish, reset };
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState("");
  const { step, start, finish, reset } = useStepProgress(loading);
  const resultsRef = useRef<HTMLDivElement>(null);

  const handleAnalyze = async () => {
    if (!file) return;

    setLoading(true);
    setResult(null);
    setError("");
    start();

    const form = new FormData();
    form.append("file", file);

    try {
      const { data } = await axios.post<AnalysisResult>(`${API_BASE}/analyze`, form, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 300_000,
      });

      finish();

      // Small delay so "done" state is visible
      setTimeout(() => {
        setResult(data);
        setLoading(false);
        setTimeout(() => {
          resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 200);
      }, 600);
    } catch (err: any) {
      reset();
      setLoading(false);
      const msg =
        err.response?.data?.detail ||
        (err.code === "ECONNABORTED" ? "Request timed out. Try a smaller document." : "Something went wrong. Please try again.");
      setError(msg);
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError("");
    reset();
  };

  const showUpload = !loading && !result;
  const showProcessing = loading;
  const showResults = !!result;

  return (
    <>
      <Head>
        <title>LexClear — Understand Indian Laws in Plain English</title>
      </Head>

      <div className="min-h-screen relative" style={{ background: "#060810" }}>
        {/* Background mesh gradients */}
        <div
          className="fixed inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse 70% 40% at 50% -10%, rgba(244,200,66,0.07) 0%, transparent 60%), " +
              "radial-gradient(ellipse 50% 50% at 90% 80%, rgba(52,211,153,0.04) 0%, transparent 50%)",
          }}
        />

        <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 lg:py-16">
          {/* Header */}
          <motion.header
            className="text-center mb-14"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="flex items-center justify-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-2xl bg-gold-400/10 border border-gold-400/20 flex items-center justify-center">
                <Scale className="w-5 h-5 text-gold-400" />
              </div>
              <span className="font-display text-xl font-semibold text-white tracking-tight">LexClear</span>
            </div>

            <h1 className="font-display text-4xl sm:text-5xl font-bold text-white leading-tight mb-4">
              Indian Laws,{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold-400 to-gold-600">
                Plain & Simple
              </span>
            </h1>
            <p className="text-slate-400 text-base sm:text-lg max-w-xl mx-auto leading-relaxed">
              Upload any parliamentary bill, act, or policy document.
              We&apos;ll extract what actually matters — in plain English.
            </p>
          </motion.header>

          {/* Main card */}
          <AnimatePresence mode="wait">
            {showUpload && (
              <motion.div
                key="upload"
                className="glass rounded-3xl p-8 sm:p-10 border border-white/6 max-w-xl mx-auto"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4 }}
              >
                <UploadZone onFile={(f) => { setFile(f); setError(""); }} disabled={loading} />

                <AnimatePresence>
                  {error && (
                    <motion.div
                      className="mt-4 flex items-start gap-2.5 p-4 rounded-xl bg-scarlet-400/8 border border-scarlet-400/20"
                      initial={{ opacity: 0, y: -6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                    >
                      <AlertTriangle className="w-4 h-4 text-scarlet-400 shrink-0 mt-0.5" />
                      <p className="text-sm text-scarlet-400">{error}</p>
                    </motion.div>
                  )}
                </AnimatePresence>

                <motion.button
                  className={`
                    w-full mt-6 py-3.5 rounded-2xl font-semibold text-sm transition-all
                    ${file
                      ? "bg-gold-400 text-ink-950 hover:bg-gold-500 active:scale-[0.98]"
                      : "bg-white/5 text-slate-600 cursor-not-allowed border border-white/6"
                    }
                  `}
                  disabled={!file}
                  onClick={handleAnalyze}
                  whileTap={file ? { scale: 0.97 } : {}}
                >
                  {file ? "Analyze Document →" : "Select a document to begin"}
                </motion.button>

                <p className="text-center text-xs text-slate-600 mt-4">
                  Works only for legal & policy documents · Free to use
                </p>
              </motion.div>
            )}

            {showProcessing && (
              <motion.div
                key="processing"
                className="glass rounded-3xl p-10 border border-white/6 max-w-sm mx-auto"
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.96 }}
                transition={{ duration: 0.4 }}
              >
                <p className="text-xs font-medium text-slate-500 uppercase tracking-widest mb-2">Processing</p>
                <h2 className="font-display text-xl font-semibold text-white mb-1">
                  {file?.name}
                </h2>
                <p className="text-xs text-slate-500 mb-6">
                  Compressing tokens + running AI analysis…
                </p>
                <ProcessingSteps currentStep={step} />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Results dashboard */}
          <AnimatePresence>
            {showResults && result && (
              <motion.div
                key="results"
                ref={resultsRef}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
              >
                {/* Non-legal rejection */}
                {!result.is_legal ? (
                  <div className="glass rounded-3xl p-10 border border-scarlet-400/15 max-w-xl mx-auto text-center">
                    <div className="w-14 h-14 rounded-2xl bg-scarlet-400/10 border border-scarlet-400/20 flex items-center justify-center mx-auto mb-4">
                      <AlertTriangle className="w-7 h-7 text-scarlet-400" />
                    </div>
                    <h2 className="font-display text-xl font-semibold text-white mb-2">Not a Legal Document</h2>
                    <p className="text-sm text-slate-400 leading-relaxed">{result.summary}</p>
                    <button
                      onClick={handleReset}
                      className="mt-6 flex items-center gap-2 text-sm text-gold-400 hover:text-gold-300 mx-auto transition-colors"
                    >
                      <RefreshCw className="w-4 h-4" /> Try another document
                    </button>
                  </div>
                ) : (
                  <>
                    {/* Results header */}
                    <div className="flex items-center justify-between mb-8">
                      <div>
                        <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Analysis Complete</p>
                        <h2 className="font-display text-2xl sm:text-3xl font-bold text-white">
                          Here&apos;s what actually matters
                        </h2>
                      </div>
                      <button
                        onClick={handleReset}
                        className="flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-colors glass px-3 py-2 rounded-xl"
                      >
                        <RefreshCw className="w-3.5 h-3.5" /> New doc
                      </button>
                    </div>

                    {/* Token stats — always prominent */}
                    <div className="mb-6">
                      <TokenStats
                        originalTokens={result.original_tokens}
                        compressedTokens={result.compressed_tokens}
                        tokensSaved={result.tokens_saved}
                        fromCache={result.from_cache}
                      />
                    </div>

                    {/* Summary row — full width */}
                    <div className="mb-6">
                      <SummaryCard
                        summary={result.summary}
                        simplifiedExplanation={result.simplified_explanation}
                        penaltiesAndCompliance={result.penalties_and_compliance}
                        documentType={result.document_type}
                      />
                    </div>

                    {/* Two column grid for detail cards */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5 auto-rows-fr">
                      <KeyChangesCard changes={result.key_changes} />
                      <AffectedEntitiesCard entities={result.affected_entities} />
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 auto-rows-fr">
                      <FinancialImpactCard impact={result.financial_impact} />
                      <TimelineCard timeline={result.timeline} />
                    </div>

                    {/* Chat interface */}
                    <div className="mb-6">
                      <ChatCard docHash={result.doc_hash} />
                    </div>

                    <p className="text-center text-xs text-slate-600 mt-8">
                      AI-generated summary · Always verify with the official gazette or a qualified lawyer.
                    </p>
                  </>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </>
  );
}
