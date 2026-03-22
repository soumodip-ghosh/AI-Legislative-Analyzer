import React, { useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, AlertCircle, X } from "lucide-react";

interface UploadZoneProps {
  onFile: (file: File) => void;
  disabled?: boolean;
}

export default function UploadZone({ onFile, disabled }: UploadZoneProps) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const validateAndSet = useCallback((file: File) => {
    setError("");
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "docx"].includes(ext || "")) {
      setError("Only PDF and DOCX files are supported.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError("File must be under 5MB.");
      return;
    }
    setSelectedFile(file);
    onFile(file);
  }, [onFile]);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      if (disabled) return;
      const file = e.dataTransfer.files[0];
      if (file) validateAndSet(file);
    },
    [disabled, validateAndSet]
  );

  const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) validateAndSet(file);
  };

  const clearFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedFile(null);
    setError("");
  };

  return (
    <div className="w-full">
      <motion.label
        htmlFor="file-input"
        className={`
          relative flex flex-col items-center justify-center w-full
          min-h-[220px] rounded-2xl border-2 border-dashed cursor-pointer
          transition-all duration-300 select-none overflow-hidden
          ${dragging ? "drop-active" : "border-white/10 hover:border-gold-400/30"}
          ${disabled ? "opacity-50 pointer-events-none" : ""}
          ${selectedFile ? "border-jade-400/40" : ""}
        `}
        style={{ background: dragging ? "rgba(244,200,66,0.03)" : "rgba(12,16,33,0.5)" }}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        whileHover={{ scale: disabled ? 1 : 1.005 }}
        whileTap={{ scale: disabled ? 1 : 0.995 }}
      >
        {/* Ambient glow on drag */}
        <AnimatePresence>
          {dragging && (
            <motion.div
              className="absolute inset-0 pointer-events-none"
              style={{ background: "radial-gradient(ellipse 60% 60% at 50% 50%, rgba(244,200,66,0.06), transparent)" }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />
          )}
        </AnimatePresence>

        <AnimatePresence mode="wait">
          {selectedFile ? (
            <motion.div
              key="selected"
              className="flex flex-col items-center gap-3 px-6 text-center"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <div className="w-14 h-14 rounded-2xl bg-jade-400/10 border border-jade-400/20 flex items-center justify-center">
                <FileText className="w-7 h-7 text-jade-400" />
              </div>
              <div>
                <p className="font-medium text-white text-sm">{selectedFile.name}</p>
                <p className="text-slate-400 text-xs mt-1">
                  {(selectedFile.size / 1024).toFixed(0)} KB · Ready to analyze
                </p>
              </div>
              <button
                onClick={clearFile}
                className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-scarlet-400 transition-colors mt-1"
              >
                <X className="w-3 h-3" /> Remove
              </button>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              className="flex flex-col items-center gap-4 px-6 text-center"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <motion.div
                className="w-14 h-14 rounded-2xl bg-gold-400/8 border border-gold-400/15 flex items-center justify-center"
                animate={{ y: [0, -4, 0] }}
                transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
              >
                <Upload className="w-7 h-7 text-gold-400/70" />
              </motion.div>
              <div>
                <p className="font-medium text-white/80 text-sm">
                  Drop your document here
                </p>
                <p className="text-slate-500 text-xs mt-1.5">
                  PDF or DOCX · Max 5MB · Parliamentary bills, Acts, Policy docs
                </p>
              </div>
              <span className="text-xs px-3 py-1.5 rounded-full border border-white/8 text-slate-400 bg-white/[0.02]">
                or click to browse
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        <input
          id="file-input"
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={handleInput}
          disabled={disabled}
        />
      </motion.label>

      <AnimatePresence>
        {error && (
          <motion.div
            className="flex items-center gap-2 mt-3 text-scarlet-400 text-sm"
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
