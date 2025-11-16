import type React from "react";

interface ToolsPanelProps {
  supplierOptions: string[];
  inspectionSupplier: string;
  inspectionMessage: string;
  inspectionError: string | null;
  inspectionResult: unknown[];
  inspectionLoading: boolean;
  onInspectionSupplierChange: (value: string) => void;
  onInspectionFileChange: (files: FileList | null) => void;
  onInspectionSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  onOverrideSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  overrideMessage: string;
  overrideError: string | null;
}

export function ToolsPanel({
  supplierOptions,
  inspectionSupplier,
  inspectionMessage,
  inspectionError,
  inspectionResult,
  inspectionLoading,
  onInspectionSupplierChange,
  onInspectionFileChange,
  onInspectionSubmit,
  onOverrideSubmit,
  overrideMessage,
  overrideError,
}: ToolsPanelProps) {
  return (
    <section id="tools" className="panel tools-grid">
      <div>
        <h3>Inspection PDF</h3>
        <p>Utiliser ce module pour vérifier rapidement une table PDF avant de mettre à jour un snapshot.</p>
        <form className="override-form" onSubmit={onInspectionSubmit}>
          <label>
            Fournisseur
            <input
              name="inspect_supplier"
              list="supplier-options"
              value={inspectionSupplier}
              onChange={(event) => onInspectionSupplierChange(event.target.value)}
              placeholder="engie"
            />
          </label>
          <datalist id="supplier-options">
            {supplierOptions.map((supplier) => (
              <option key={supplier} value={supplier} />
            ))}
          </datalist>
          <label>
            Fichier PDF
            <input type="file" accept=".pdf" onChange={(event) => onInspectionFileChange(event.target.files)} />
          </label>
          <button className="btn" type="submit" disabled={inspectionLoading}>
            {inspectionLoading ? "Analyse..." : "Inspecter"}
          </button>
        </form>
        <p className="muted">{inspectionMessage}</p>
        {inspectionError && <p className="error">{inspectionError}</p>}
        {inspectionResult.length > 0 && (
          <div className="inspect-preview">
            <p>{inspectionResult.length} lignes (aperçu des premières):</p>
            <pre>{JSON.stringify(inspectionResult.slice(0, 3), null, 2)}</pre>
          </div>
        )}
      </div>
      <div>
        <h3>Override source</h3>
        <form className="override-form" onSubmit={onOverrideSubmit}>
          <label>
            Fournisseur
            <input required name="supplier" placeholder="ex: Engie" />
          </label>
          <label>
            URL source temporaire
            <input required name="url" type="url" placeholder="https://..." />
          </label>
          <label>
            Observed at (optionnel)
            <input name="observed_at" type="date" />
          </label>
          <button className="btn" type="submit">
            Lancer override
          </button>
        </form>
        {overrideMessage && <p className="muted">{overrideMessage}</p>}
        {overrideError && <p className="error">{overrideError}</p>}
      </div>
    </section>
  );
}
