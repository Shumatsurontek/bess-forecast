import { useQuery } from '@tanstack/react-query';
import { SectionTitle } from '@/components/SectionTitle';
import { validationRepository } from '@/repositories/validationRepository';

export default function ValidationPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['validation/last'],
    queryFn: () => validationRepository.last(),
  });

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <SectionTitle
        eyebrow="data quality"
        title="Validation report"
        subtitle="Rules classify issues into BLOCKING (run aborted, fallback to last forecast) and WARNING (logged, run continues)."
      />

      {isLoading && <div className="text-muted">Loading…</div>}
      {data && (
        <>
          <div className="panel mb-6 flex gap-6">
            <div>
              <div className="text-muted text-xs uppercase tracking-widest">Blocking</div>
              <div className="num text-3xl text-red-300">{(data as any).blocking_count}</div>
            </div>
            <div>
              <div className="text-muted text-xs uppercase tracking-widest">Warnings</div>
              <div className="num text-3xl text-accent">{(data as any).warning_count}</div>
            </div>
          </div>

          <div className="panel">
            <table className="w-full text-sm">
              <thead className="text-muted text-xs uppercase tracking-widest">
                <tr><th className="text-left py-2">Rule</th><th>Severity</th><th>Affected</th><th className="text-left">Message</th></tr>
              </thead>
              <tbody>
                {(data as any).issues.map((i: any, k: number) => (
                  <tr key={k} className="border-t border-white/5">
                    <td className="py-2 font-mono">{i.rule}</td>
                    <td className="text-center">
                      <span className={i.severity === 'BLOCKING' ? 'badge-block' : 'badge-warn'}>
                        {i.severity}
                      </span>
                    </td>
                    <td className="text-center num">{i.affected_count}</td>
                    <td className="text-ink">{i.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
