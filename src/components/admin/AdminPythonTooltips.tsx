import { getLlmKeyStatus } from "@/lib/llm-status";
import { getPythonTooltipCatalog, PYTHON_TIP_COUNT } from "@/lib/python-tooltips";

export default function AdminPythonTooltips() {
  const catalog = getPythonTooltipCatalog();
  const llm = getLlmKeyStatus();

  return (
    <div className="space-y-8">
      <header>
        <p className="text-[11px] font-bold uppercase tracking-[0.35em] text-[var(--qb-accent)]">
          Python syntax tooltips
        </p>
        <p className="mt-2 text-sm text-[#8caacf]">
          {PYTHON_TIP_COUNT} patterns active on public strategy pages (hover desktop / tap mobile).
        </p>
      </header>

      <section className="rounded-2xl border border-[#55e0ff]/25 bg-[#0a1218]/50 p-6">
        <p className="text-[11px] font-bold uppercase tracking-[0.35em] text-[var(--qb-accent)]">
          AI providers (.env)
        </p>
        <ul className="mt-4 space-y-2 text-sm text-[#dbe7fb]">
          <li>
            Gemini ({llm.geminiModel}):{" "}
            <span className={llm.gemini ? "text-emerald-400" : "text-amber-300"}>
              {llm.gemini ? "Connected" : "Not configured — set GEMINI_API_KEY"}
            </span>
          </li>
          <li>
            DeepSeek ({llm.deepseekModel}):{" "}
            <span className={llm.deepseek ? "text-emerald-400" : "text-amber-300"}>
              {llm.deepseek ? "Connected" : "Not configured — set DEEPSEEK_API_KEY"}
            </span>
          </li>
          <li className="text-xs text-[#8caacf]">
            Mainland China visitors auto-route to DeepSeek when geo headers indicate CN.
          </li>
        </ul>
      </section>

      <div className="qb-admin-tooltips-table-wrap">
        <table className="qb-admin-tooltips-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Syntax</th>
              <th>Regex</th>
              <th>English explanation</th>
              <th>中文说明</th>
            </tr>
          </thead>
          <tbody>
            {catalog.map((row) => (
              <tr key={row.id}>
                <td>{row.id}</td>
                <td>
                  <code className="qb-admin-syntax">{row.syntax}</code>
                </td>
                <td>
                  <code className="qb-admin-regex">{row.pattern}</code>
                </td>
                <td className="qb-admin-tip-en">{row.en}</td>
                <td className="qb-admin-tip-zh">{row.zh}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
