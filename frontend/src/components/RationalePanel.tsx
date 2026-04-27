/** A small inline explainer that ties the metric KPIs back to the business case. */
export function RationalePanel() {
  return (
    <details className="panel mb-6 group">
      <summary className="cursor-pointer flex items-center justify-between">
        <span className="font-serif text-lg text-chalk">
          Why these stages, why these metrics?
        </span>
        <span className="text-muted text-sm group-open:rotate-180 transition-transform">⌃</span>
      </summary>
      <div className="mt-4 grid md:grid-cols-2 gap-6 text-sm leading-relaxed text-ink/85">
        <section>
          <h3 className="text-accent font-mono uppercase tracking-widest text-xs mb-2">
            Use case
          </h3>
          <p>
            The forecast feeds a <strong>peak-shaving controller</strong>. Missing a peak means
            paying the demand charge that day; over-forecasting wastes battery cycles.
            Errors are <em>asymmetric</em>, so the loss is too.
          </p>
        </section>
        <section>
          <h3 className="text-accent font-mono uppercase tracking-widest text-xs mb-2">
            Why pinball loss with α = 0.75?
          </h3>
          <p>
            Quantile regression at q=0.75 nudges the predictions slightly upward in
            uncertain regions — the model is rewarded for crossing the peak threshold
            <em> when in doubt</em>, exactly when the controller needs it to.
          </p>
        </section>
        <section>
          <h3 className="text-accent font-mono uppercase tracking-widest text-xs mb-2">
            Why "fail safely"?
          </h3>
          <p>
            Validation rules classify issues into BLOCKING and WARNING. A BLOCKING
            issue aborts the run; the controller falls back to the previous forecast
            instead of consuming bad data. The repair stage drops sentinels, clips
            negatives and ffills short gaps so a single dirty sample doesn't take the
            day down.
          </p>
        </section>
        <section>
          <h3 className="text-accent font-mono uppercase tracking-widest text-xs mb-2">
            Peak Capture Rate
          </h3>
          <p>
            Hover the four KPI tiles. The headline is <strong>peak capture</strong> —
            of the actual peaks above 85% of max(actuals), how many did we predict
            above the same threshold? RMSE alone hides the asymmetry; this metric
            doesn't.
          </p>
        </section>
      </div>
    </details>
  );
}
