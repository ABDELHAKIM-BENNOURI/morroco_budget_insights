import { useEffect, useState } from 'react';

/**
 * usePlotlyFigure(name)
 *   name : "sankey_figure" | "treemap_figure" (sans extension)
 *
 * Charge un fichier figure Plotly produit par les scripts Python
 * (04_sankey.py / 05_treemap.py) puis copié dans /public/data/ par
 * le hook prebuild (scripts/copy-data.mjs).
 *
 * Renvoie { figure, error, loading }.
 *   - figure  : { data, layout, ... } prêt à passer à <Plot> ;
 *   - error   : message lisible si fetch ou parsing échoue ;
 *   - loading : true tant que ni figure ni error n'ont été résolus.
 */
export function usePlotlyFigure(name) {
  const [figure, setFigure]   = useState(null);
  const [error, setError]     = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setFigure(null);
    setError(null);
    setLoading(true);

    const url = `${import.meta.env.BASE_URL}data/${name}.json`;
    fetch(url, { cache: 'no-store' })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status} sur ${url}`);
        return r.json();
      })
      .then((json) => {
        if (cancelled) return;
        if (!json || !Array.isArray(json.data) || !json.layout) {
          throw new Error(`Schema Plotly inattendu pour ${name}`);
        }
        setFigure(json);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e.message || String(e));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [name]);

  return { figure, error, loading };
}
