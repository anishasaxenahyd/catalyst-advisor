import type { ScenarioDataset } from "../../types/scenario";

export default function DatasetPreviewTable({ dataset }: { dataset: ScenarioDataset }) {
  return (
    <div className="data-table-wrap">
      <p className="table-title">{dataset.name}</p>
      <p className="table-description">{dataset.description}</p>
      <table className="data-table">
        <thead>
          <tr>
            {dataset.columns.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {dataset.rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td key={j} data-label={dataset.columns[j]}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
