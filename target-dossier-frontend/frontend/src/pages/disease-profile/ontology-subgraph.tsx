import { withContentRect } from "react-measure";
import { line as d3Line, max, curveMonotoneX } from "d3";
import {
  layeringLongestPath,
  decrossTwoLayer,
  coordCenter,
  sugiyama,
  dagStratify,
} from "d3-dag";
// import { Link } from "react-router-dom";
import React from "react";
import OntologyTooltip from "./ontology-tooltip";
import { Empty } from "antd";



interface OntologySubgraphProps {
  dagData:any
  measureRef: React.RefObject<HTMLDivElement>;
  name: string;
  contentRect: {
    bounds: {
      width: number;
    };
  };
}

// function getAncestors(efoId: string, idToDisease: Record<string, Disease>): Array<Disease & { nodeType: string }> {
//   const ancestors: Array<Disease & { nodeType: string }> = [{ ...idToDisease[efoId], nodeType: "anchor" }];
//   const queue: string[] = [efoId];
//   const visited: Set<string> = new Set([efoId]);

//   while (queue.length > 0) {
//     const id = queue.shift()!;
//     const node = idToDisease[id];

//     node.parentIds.forEach((parentId) => {
//       if (!visited.has(parentId)) {
//         ancestors.push({ ...idToDisease[parentId], nodeType: "ancestor" });
//         queue.push(parentId);
//         visited.add(parentId);
//       }
//     });
//   }

//   return ancestors;
// }

// function buildDagData(efoId: string, efo: Disease[], idToDisease: Record<string, Disease>): Array<Disease & { nodeType: string }> {
//   const dag: Array<Disease & { nodeType: string }> = [];

//   efo.forEach((disease) => {
//     if (disease.parentIds.includes(efoId)) {
//       dag.push({
//         id: disease.id,
//         name: disease.name,
//         parentIds: [efoId],
//         nodeType: "child",
//       });
//     }
//   });

//   const ancestors = getAncestors(efoId, idToDisease);
//   ancestors.forEach((ancestor) => {
//     dag.push(ancestor);
//   });

//   return dag;
// }

const layering = layeringLongestPath();
const decross = decrossTwoLayer();
const coord = coordCenter();

const helperLayout = sugiyama()
  .layering(layering)
  .decross(decross)
  .coord(coord);

function textWithEllipsis(text: string, threshold: number): string {
  return text.length <= threshold ? text : `${text.slice(0, threshold)}...`;
}

function getMaxLayerCount(dag: any): number {
  helperLayout(dag);

  const counts: Record<number, number> = {};
  let maxCount = Number.NEGATIVE_INFINITY;

  dag.descendants().forEach((node: any) => {
    const { layer } = node;

    if (counts[layer]) {
      counts[layer] += 1;
    } else {
      counts[layer] = 1;
    }

    if (counts[layer] > maxCount) {
      maxCount = counts[layer];
    }
  });

  dag.links().forEach((link: any) => {
    link.points.forEach((_: any, i: number) => {
      const index = link.source.layer + i;
      counts[index] += 1;
      if (counts[index] > maxCount) {
        maxCount = counts[index];
      }
    });
  });

  return maxCount;
}

const colorMap: Record<string, string> = {
  anchor: "#1F2F98",
  ancestor: "#787FF6",
  child: "#1CA7EC",
};
const diameter: number = 12;
const radius: number = diameter / 2;
const yOffset: number = 100;
const line = d3Line().curve(curveMonotoneX);



const OntologySubgraph: React.FC<OntologySubgraphProps> = ({
  dagData,
  name,
  measureRef,
  contentRect,
}) => {

  console.log("dagData", dagData);
  if(dagData.length==0) return <Empty description="No Data Available" />;
  const { width } = contentRect.bounds;

  // const dagData = buildDagData(efoId, efo, idToDisease);
  const dag = dagStratify()(dagData);
  const maxLayerCount = getMaxLayerCount(dag);
  const height = maxLayerCount * 6;
  const layout = sugiyama()
    .layering(layering)
    .decross(decross)
    .coord(coord)
    .nodeSize(() => {
      const base = diameter + 3;
      return [base, base];
    })
    .size([height, width]);

  layout(dag);
  const nodes = dag.descendants();
  const links = dag.links();
  const separation = width / (max(nodes, (d: any) => d.layer) + 1);
  const xOffset = separation / 2 - radius;
  const textLimit = separation / 8;

  line.x((d: any) => d.y - xOffset).y((d: any) => d.x);

  return (
    <div ref={measureRef} >
      {width ? (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          xmlnsXlink="http://www.w3.org/1999/xlink"
          width={width}
          height={height + yOffset}
        >
          <defs>
            <marker
              id="arrowhead"
              orient="auto"
              markerWidth="2"
              markerHeight="4"
              refX="0.1"
              refY="2"
            >
              <path d="M0,0 V4 L2,2 Z" fill="#5a5f5f" />
            </marker>
          </defs>
          <g transform="translate(0, 10)">
            <rect
              x="4"
              y="11"
              width={diameter}
              height={diameter}
              fill="none"
              stroke="#e0e0e0"
              strokeWidth="2"
            />
            <text
              x="20"
              y="17"
              fill="#5a5f5f"
              dominantBaseline="middle"
              fontSize="12"
            >
              therapeutic area
            </text>
            <circle
              cx="10"
              cy="34"
              r={radius}
              fill="none"
              stroke="#e0e0e0"
              strokeWidth="2"
            />
            <text
              fill="#5a5f5f"
              x="20"
              y="34"
              dominantBaseline="middle"
              fontSize="12"
            >
              disease
            </text>
            <circle
              cx="150"
              cy="0"
              r={radius}
              fill={colorMap.child}
              stroke="#e0e0e0"
            />
            <text
              fill="#5a5f5f"
              x="160"
              y="0"
              dominantBaseline="middle"
              fontSize="12"
            >
              descendants
            </text>
            <circle
              cx="150"
              cy="17"
              r={radius}
              fill={colorMap.ancestor}
              stroke="#e0e0e0"
            />
            <text
              fill="#5a5f5f"
              x="160"
              y="17"
              dominantBaseline="middle"
              fontSize="12"
            >
              ancestors
            </text>
            <circle
              cx="150"
              cy="34"
              r={radius}
              fill={colorMap.anchor}
              stroke="#e0e0e0"
            />
            <text
              fill="#5a5f5f"
              x="160"
              y="34"
              dominantBaseline="middle"
              fontSize="12"
            >
              {name}
            </text>
          </g>
          <g transform={`translate(${width / 2}, 70)`}>
            <text
              x="-160"
              fontWeight="bold"
              fontSize="14"
              fill="#5a5f5f"
              dominantBaseline="middle"
            >
              GENERAL
            </text>
            <text
              x="100"
              fontWeight="bold"
              fontSize="14"
              fill="#5a5f5f"
              dominantBaseline="middle"
            >
              SPECIFIC
            </text>
            <path
              markerEnd="url(#arrowhead)"
              strokeWidth="2"
              fill="none"
              stroke="#5a5f5f"
              d="M-80,0 L80,0"
            />
          </g>
          <g transform={`translate(0, ${yOffset})`}>
            {links.map(({ points, source, target }: any) => (
              <path
                key={`${source.id}-${target.id}`}
                d={line(points)}
                fill="none"
                strokeWidth="2"
                stroke="#D8DCD6"
              />
            ))}
          </g>
          <g transform={`translate(0, ${yOffset})`}>
            {nodes.map((node: any) => (
  <OntologyTooltip title={`${node.data.name || "No name"} | ID: ${node.id}`}>


              <g key={node.id}>
                <text
                  x={node.y - xOffset}
                  y={node.x}
                  dx="9"
                  fontSize="12"
                  dominantBaseline="middle"
                  fill="#5a5f5f"
                  style={{ cursor: "pointer" }}
                >
                  <title>{node.data.name}</title>
                  {textWithEllipsis(node.data.name || "No name", textLimit)}
                </text>

                {node.data.parentIds.length === 0 ? (
                  <rect
                    x={node.y - radius - xOffset}
                    y={node.x - radius}
                    width={diameter}
                    height={diameter}
                    fill={colorMap[node.data.nodeType]}
                    stroke="#e0e0e0"
                  />
                ) : (
                  <circle
                    cx={node.y - xOffset}
                    cy={node.x}
                    r={radius}
                    fill={colorMap[node.data.nodeType]}
                    stroke="#e0e0e0"
                  />
                )}
              </g>
              </OntologyTooltip>

            ))}
          </g>
        </svg>
      ) : null}
    </div>
  );
}

export default withContentRect("bounds")(OntologySubgraph);