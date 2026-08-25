import JsonLd from "@/components/JsonLd";
import { faqJsonLd } from "@/lib/seo";

type Faq = { question: string; answer: string };

export default function SeoFaqSection({
  title,
  faqs,
}: {
  title: string;
  faqs: Faq[];
}) {
  if (faqs.length === 0) return null;

  return (
    <section className="qb-seo-faq" aria-labelledby="qb-seo-faq-title">
      <JsonLd data={faqJsonLd(faqs)} />
      <h2 id="qb-seo-faq-title" className="qb-seo-faq-title">
        {title}
      </h2>
      <div className="qb-seo-faq-list">
        {faqs.map((faq) => (
          <details key={faq.question} className="qb-seo-faq-item">
            <summary>{faq.question}</summary>
            <p>{faq.answer}</p>
          </details>
        ))}
      </div>
    </section>
  );
}
