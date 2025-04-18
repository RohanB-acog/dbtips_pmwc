import { useState, useEffect } from "react";
import { useQuery } from "react-query";
import LoadingButton from "../../components/loading";
import { fetchData } from "../../utils/fetchData";
import { Empty } from "antd";
import { useLocation } from "react-router-dom";
import { parseQueryParams } from "../../utils/parseUrlParams";
import Graph from "./dgpg-graph";

const GraphComponent = () => {
  const location = useLocation();
  const [target, setTarget] = useState("");
  const [elements, setElements] = useState([]);
  const [indications, setIndications] = useState([]);

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const { target, indications } = parseQueryParams(queryParams);
    setTarget(target);
    setIndications(indications);
  }, [location.search]);

  const payload = {
    target_gene: target,
    target_diseases: indications,
    metapath: "DGPG",
  };

  const {
    error,
    isLoading,
  } = useQuery(
    ["graphData", payload],
    () => fetchData(payload, "/fetch-graph/"),
    {
      enabled: !!target && !!indications.length,
      onSuccess: (data) => {
        const nodes = data.elements.filter((el) => el.data && el.data.id);
        const nodesIds = nodes.map((el) => el.data.id);
        const edges = data.elements.filter(
          (el) => el.data && el.data.target && nodesIds.includes(el.data.target)
        );

        setElements([...nodes, ...edges]);
      },
    }
  );

  return (
    <div>
      {(isLoading || error || elements.length === 0) && (
        <section
          id="knowledge-graph-evidence"
          className="px-[5vw] py-20 bg-gray-50 mt-12"
        >
          <h1 className="text-3xl font-semibold">Network Biology</h1>
          <p className="mt-2">
            This knowledge graph section visualizes the connections between a
            single target and multiple disease pathways, illustrating how
            alterations in this target may impact various disease processes.
          </p>
          <h2 className="text-xl subHeading font-semibold mt-2">Metapath description:</h2>
          <p className="mt-2">
            Disease(s) → (genetically associated with) → Genes → (actively
            involved in) → Pathway → (actively involved in) → Target ({target})
            <br /> This metapath is used to reduce the inherently complex nature
            of the graph and enable the identification of pathways involving both
            disease(s) associated genes and the target of interest.
          </p>
          {isLoading && <LoadingButton />}
          {error && <Empty description="Error loading data" />}
          {!isLoading && !error && elements.length === 0 && (
            <div className="h-[280px] flex items-center justify-center">
            <Empty description="No data available" />
            </div>
          )}
        </section>
      )}
      {!isLoading && !error && elements.length > 0 && (
        <Graph json={{ elements }} target={target} />
      )}
    </div>
  );
};

export default GraphComponent;
