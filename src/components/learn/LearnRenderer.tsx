import type { LearnBlock } from "@/lib/learn/types";

import LearnVisual from "./LearnVisual";

function renderInline(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={i} className="qb-docs-inline-code">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

function LearnBlockView({ block }: { block: LearnBlock }) {
  switch (block.kind) {
    case "p":
      return <p className="qb-docs-p">{renderInline(block.text)}</p>;
    case "h2":
      return <h2 className="qb-docs-h2">{block.text}</h2>;
    case "h3":
      return <h3 className="qb-docs-h3">{block.text}</h3>;
    case "ul":
      return (
        <ul className="qb-docs-ul">
          {block.items.map((item) => (
            <li key={item.slice(0, 40)}>{renderInline(item)}</li>
          ))}
        </ul>
      );
    case "ol":
      return (
        <ol className="qb-docs-ol">
          {block.items.map((item) => (
            <li key={item.slice(0, 40)}>{renderInline(item)}</li>
          ))}
        </ol>
      );
    case "code":
      return (
        <pre className="qb-docs-pre">
          <code className={`language-${block.lang ?? "python"}`}>{block.code}</code>
        </pre>
      );
    case "note":
      return (
        <aside className="qb-docs-callout qb-docs-callout-note" role="note">
          <strong>Note.</strong> {renderInline(block.text)}
        </aside>
      );
    case "warn":
      return (
        <aside className="qb-docs-callout qb-docs-callout-warn" role="note">
          <strong>Important.</strong> {renderInline(block.text)}
        </aside>
      );
    case "table":
      return (
        <div className="qb-docs-table-wrap">
          <table className="qb-docs-table">
            <thead>
              <tr>
                {block.headers.map((h) => (
                  <th key={h}>{renderInline(h)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {block.rows.map((row) => (
                <tr key={row.join("|").slice(0, 48)}>
                  {row.map((cell) => (
                    <td key={cell.slice(0, 24)}>{renderInline(cell)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    case "visual":
      return (
        <div className="qb-learn-visual-wrap">
          <LearnVisual id={block.id} />
        </div>
      );
    case "checklist":
      return (
        <div className="qb-learn-checklist">
          <h3 className="qb-docs-h3">{block.title}</h3>
          <ul className="qb-learn-checklist-items">
            {block.items.map((item) => (
              <li key={item.slice(0, 40)}>
                <span className="qb-learn-check" aria-hidden>
                  ✓
                </span>
                {renderInline(item)}
              </li>
            ))}
          </ul>
        </div>
      );
    default:
      return null;
  }
}

export default function LearnRenderer({ blocks }: { blocks: LearnBlock[] }) {
  return (
    <div className="qb-docs-body">
      {blocks.map((block, idx) => (
        <LearnBlockView key={`${block.kind}-${idx}`} block={block} />
      ))}
    </div>
  );
}
