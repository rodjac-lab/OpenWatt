import type { SupplierRow } from "../../app/admin/types";

interface SuppliersPanelProps {
  supplierRows: SupplierRow[];
}

export function SuppliersPanel({ supplierRows }: SuppliersPanelProps) {
  return (
    <section id="suppliers" className="panel">
      <header className="panel__header">
        <div>
          <h2>Fournisseurs & parsers</h2>
          <p>Liste extraite des observations en base.</p>
        </div>
        <button className="btn btn--ghost">Ajouter un fournisseur</button>
      </header>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Fournisseur</th>
              <th>Parser</th>
              <th>Source</th>
              <th>Observations</th>
              <th>Statuts</th>
            </tr>
          </thead>
          <tbody>
            {supplierRows.map((row) => (
              <tr key={row.supplier}>
                <td>{row.supplier}</td>
                <td>{row.parser_version ?? "?"}</td>
                <td className="truncate">
                  <a href={row.source_url} target="_blank" rel="noreferrer">
                    {row.source_url ?? "?"}
                  </a>
                </td>
                <td>{row.observations}</td>
                <td>
                  {row.statuses.map((status) => (
                    <span key={status} className="badge badge--grey">
                      {status}
                    </span>
                  ))}
                </td>
              </tr>
            ))}
            {supplierRows.length === 0 && (
              <tr>
                <td colSpan={5}>Aucune observation chargée.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
