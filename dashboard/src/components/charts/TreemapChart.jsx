import { useMemo } from 'react';
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js-dist-min';
import { usePlotlyFigure } from '../../hooks/usePlotlyFigure.js';

const Plot = createPlotlyComponent(Plotly);

const HEIGHT = 720;

export default function TreemapChart() {
  const { figure, error, loading } = usePlotlyFigure('treemap_figure');

  const layout = useMemo(() => {
    if (!figure) return null;
    return {
      ...figure.layout,
      autosize: true,
      margin: { ...(figure.layout.margin || {}), l: 12, r: 12 },
    };
  }, [figure]);

  if (loading) {
    return (
      <div
        className="card flex items-center justify-center text-muted text-sm"
        style={{ height: HEIGHT }}
      >
        Chargement du Treemap…
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="card flex items-center justify-center text-emprunt text-sm p-6 text-center"
        style={{ height: HEIGHT }}
      >
        Impossible de charger treemap_figure.json — {error}.
        <br />
        Vérifiez que le pipeline Python a bien été exécuté.
      </div>
    );
  }

  return (
    <div className="card p-2">
      <Plot
        data={figure.data}
        layout={layout}
        config={{ displaylogo: false, responsive: true, displayModeBar: 'hover' }}
        useResizeHandler
        style={{ width: '100%', height: HEIGHT }}
      />
    </div>
  );
}
