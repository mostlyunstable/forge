import { useEffect, useRef, useState } from 'react';
import { useDecisions, useBugs, useAnalysisReports } from '@/hooks/useApi';
import { useSettings } from '@/stores/settings';
import * as d3 from 'd3';
import { SkeletonRow } from '@/components/ui/SkeletonRow';
import { ErrorState } from '@/components/ui/ErrorState';
import { ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  type: 'decision' | 'bug' | 'report';
}

interface GraphLink {
  source: string;
  target: string;
}

export function GraphView() {
  const currentProjectId = useSettings((s) => s.currentProjectId);
  const decisionsQuery = useDecisions(currentProjectId);
  const bugsQuery = useBugs(currentProjectId);
  const reportsQuery = useAnalysisReports(currentProjectId);

  const svgRef = useRef<SVGSVGElement>(null);
  const [zoom, setZoom] = useState(1);

  const isLoading = decisionsQuery.isLoading || bugsQuery.isLoading;

  useEffect(() => {
    if (!svgRef.current || isLoading) return;

    const decisions = decisionsQuery.data?.decisions ?? [];
    const bugs = bugsQuery.data?.bugs ?? [];
    const reports = reportsQuery.data?.reports ?? [];

    const nodes: GraphNode[] = [
      ...decisions.map((d) => ({ id: d.id, label: d.title, type: 'decision' as const })),
      ...bugs.map((b) => ({ id: b.id, label: b.title, type: 'bug' as const })),
      ...reports.map((r) => ({ id: r.id, label: r.title, type: 'report' as const })),
    ];

    const links: GraphLink[] = [];
    // Create some basic links between related items
    decisions.forEach((d, i) => {
      if (i > 0) links.push({ source: decisions[i - 1].id, target: d.id });
    });
    bugs.forEach((b, i) => {
      if (i > 0) links.push({ source: bugs[i - 1].id, target: b.id });
    });

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    const g = svg.append('g');

    const simulation = d3.forceSimulation<GraphNode>(nodes)
      .force('link', d3.forceLink<GraphNode, GraphLink>(links).id((d) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#2A2A3A')
      .attr('stroke-width', 1);

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const dragBehavior = d3.drag<any, GraphNode>()
      .on('start', (event: any, d: GraphNode) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event: any, d: GraphNode) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event: any, d: GraphNode) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    const node = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .call(dragBehavior);

    node.append('circle')
      .attr('r', 6)
      .attr('fill', (d) => {
        switch (d.type) {
          case 'decision': return '#4A4AFF';
          case 'bug': return '#EF4444';
          case 'report': return '#06B6D4';
        }
      })
      .attr('stroke', 'none');

    node.append('text')
      .text((d) => d.label)
      .attr('x', 10)
      .attr('y', 4)
      .attr('font-size', '11px')
      .attr('fill', '#8888AA')
      .attr('font-family', 'var(--font-mono)');

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as unknown as GraphNode).x!)
        .attr('y1', (d) => (d.source as unknown as GraphNode).y!)
        .attr('x2', (d) => (d.target as unknown as GraphNode).x!)
        .attr('y2', (d) => (d.target as unknown as GraphNode).y!);

      node.attr('transform', (d) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [isLoading, decisionsQuery.data, bugsQuery.data, reportsQuery.data]);

  const handleZoom = (delta: number) => {
    setZoom((z) => Math.max(0.25, Math.min(4, z + delta)));
  };

  return (
    <div className="flex h-full flex-col">
      <div className="px-6 pt-6 pb-4">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-display-sm">Knowledge Graph</h1>
          <div className="flex items-center gap-2">
            <button onClick={() => handleZoom(0.25)} className="btn btn-ghost p-2">
              <ZoomIn className="h-[14px] w-[14px]" />
            </button>
            <button onClick={() => handleZoom(-0.25)} className="btn btn-ghost p-2">
              <ZoomOut className="h-[14px] w-[14px]" />
            </button>
            <button onClick={() => setZoom(1)} className="btn btn-ghost p-2">
              <RotateCcw className="h-[14px] w-[14px]" />
            </button>
          </div>
        </div>

        <div className="memory-pulse memory-pulse--active mb-6" />
      </div>

      <div className="flex-1 relative bg-[var(--color-bg-base)]">
        {isLoading ? (
          <div className="p-6"><SkeletonRow lines={5} /></div>
        ) : (decisionsQuery.data?.decisions.length ?? 0) + (bugsQuery.data?.bugs.length ?? 0) === 0 ? (
          <ErrorState
            code="EMPTY"
            message="No data to visualize. Record decisions and bugs first."
          />
        ) : (
          <svg
            ref={svgRef}
            className="w-full h-full"
            style={{ transform: `scale(${zoom})` }}
          />
        )}

        {/* Legend */}
        <div className="absolute bottom-4 left-4 rounded-[4px] border border-[var(--color-border-default)] bg-[var(--color-bg-surface)] p-3">
          <div className="text-label mb-2">Legend</div>
          <div className="space-y-1 text-[11px]">
            {[
              { color: '#4A4AFF', label: 'Decision' },
              { color: '#06B6D4', label: 'Report' },
              { color: '#EF4444', label: 'Bug' },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full" style={{ background: item.color }} />
                <span className="text-[var(--color-text-muted)]">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}