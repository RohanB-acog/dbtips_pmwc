import React, { useState, useEffect } from "react";
import { Empty, Select, Collapse, theme } from "antd";
import { CaretRightOutlined } from "@ant-design/icons";
import { useQuery } from "react-query";
import LoadingButton from "../../components/loading";
import CarouselComponent from "./carousel";
import { fetchData } from "../../utils/fetchData";
import { capitalizeFirstLetter } from "../../utils/helper";

// Utility function to convert strings to Title Case

// TypeScript Interfaces
interface GeneResult {
  gene_symbols: string[];
}

interface NetworkBiologyData {
  [disease: string]: {
    results: GeneResult[];
  };
}

interface FilteredDiseaseData {
  disease: string;
  results: GeneResult[];
}

interface NetworkBiologyProps {
  indications: string[];
}

const NetworkBiology: React.FC<NetworkBiologyProps> = ({ indications }) => {
  const { token } = theme.useToken();
  const [selectedTarget, setSelectedTarget] = useState<string | undefined>(
    undefined
  );
  const [filteredData, setFilteredData] = useState<FilteredDiseaseData[]>([]);
  const [geneSet, setGeneSet] = useState<string[]>([]);
  const [summary, setSummary] = useState<React.ReactNode>(null);

  const payload = { diseases: indications };

  const {
    data: networkBiologyData,
    error: networkBiologyError,
    isLoading: networkBiologyLoading,
  } = useQuery<NetworkBiologyData>(
    ["networkBiology", payload],
    () => fetchData(payload, "/evidence/network-biology/"),
    { enabled: indications.length > 0 ,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
      refetchOnMount: false,
    }

  );

  // Collapse Panel Styling
  const panelStyle: React.CSSProperties = {
    marginBottom: 5,
    background: "rgb(235 235 235)",
    borderRadius: token.borderRadiusLG,
    border: "none",
    fontFamily: "Poppins",
    padding: "0.3rem 0",
  };

  // Extract unique gene symbols from networkBiologyData
  useEffect(() => {
    if (networkBiologyData) {
      const genes = Array.from(
        new Set(
          Object.values(networkBiologyData).flatMap((condition) =>
            condition.results.flatMap((result) =>
              result?.gene_symbols.map((symbol) => symbol.toUpperCase())
            )
          )
        )
      );

      setGeneSet(genes);
    }
  }, [networkBiologyData]); // Add dependency array to trigger effect when networkBiologyData changes
  

  // Filter disease data based on selected target
  useEffect(() => {
    if (!networkBiologyData) return;

    const filtered = selectedTarget
      ? Object.entries(networkBiologyData)
          .map(([disease, diseaseData]) => ({
            disease,
            results: diseaseData.results.filter((result) =>
              result.gene_symbols.some(
                (gene) => gene.toUpperCase() === selectedTarget.toUpperCase()
              )
            ),
          }))
          .filter((disease) => disease.results.length > 0)
      : Object.entries(networkBiologyData).map(([disease, diseaseData]) => ({
          disease,
          results: diseaseData.results,
        }));

    setFilteredData(filtered);
  }, [selectedTarget, networkBiologyData]);

  // Handle Target Selection Change
  const handleTargetChange = (target?: string) => {
    setSelectedTarget(target);
  };

  useEffect(() => {
    if (!networkBiologyData) {
      setSummary("");
      return;
    }

    if (selectedTarget) {
      // Summary for the selected target
      const summaryJSX = (
        <>
          <span>{selectedTarget}</span> is present in{" "}
          {filteredData.map(({ disease, results }, index) => (
            <span key={index}>
              <span className="text-sky-600">{results.length}</span> pathway
              figure{results.length > 1 ? "s" : ""} of{" "}
              <span>{capitalizeFirstLetter(disease)}</span>
              {index < filteredData.length - 1 ? ", " : "."}
            </span>
          ))}
        </>
      );
      setSummary(summaryJSX);
    } else {
      // Summary for all diseases
      const summaryJSX = (
        <>
          There are{" "}
          {Object.entries(networkBiologyData).map(
            ([disease, diseaseData], index) => (
              <span key={index}>
                <span className="text-sky-600">
                  {diseaseData.results.length}
                </span>{" "}
                pathway figure{diseaseData.results.length > 1 ? "s" : ""} of{" "}
                <span>{capitalizeFirstLetter(disease)}</span>
                {index < Object.entries(networkBiologyData).length - 1
                  ? ", "
                  : "."}
              </span>
            )
          )}
        </>
      );
      setSummary(summaryJSX);
    }
  }, [selectedTarget, filteredData, networkBiologyData]);

  return (
    <section
      id="knowledge-graph-evidence"
      className="px-[5vw] py-20 bg-gray-50 mt-12"
    >
      <h1 className="text-3xl font-semibold">Disease pathways</h1>
      <p className="mt-2">
        This section offers insights into pathways relevant to disease
        pathophysiology and enables users to search disease-related pathways by
        genes across one or multiple diseases and visualize their
        interconnections.
      </p>

      {indications.length > 0 && (
        <div className="my-3">
          <span className="mt-4">Filter by gene: </span>
          <Select
            style={{ width: 300 }}
            showSearch
            placeholder="Select a gene"
            onChange={handleTargetChange}
            allowClear
           options= {geneSet.map((gene) => (
              {label: gene, value: gene}
            )).sort((a, b) => a.label.localeCompare(b.label))}/>
        </div>
      )}
      {summary && (
        <div className="my-5">
          <span className="font-bold">Summary: </span>
          <span className="text-lg">{summary}</span>
        </div>
      )}

      <div>
        {networkBiologyLoading ? (
          <div className="flex justify-center items-center">
            <LoadingButton />
          </div>
        ) : networkBiologyError ? (
          <div className="h-[70vh] flex justify-center items-center">
            <Empty description={`${networkBiologyError}`} />
          </div>
        ) : filteredData.length > 0 ? (
          <Collapse
            defaultActiveKey={filteredData.map((_, idx) => String(idx + 1))}
            expandIcon={({ isActive }) => (
              <CaretRightOutlined rotate={isActive ? 90 : 0} />
            )}
            bordered={false}
          >
            {filteredData.map((diseaseData, index) => (
              <Collapse.Panel
                key={String(index + 1)}
                header={capitalizeFirstLetter(diseaseData.disease)}
                style={panelStyle}
              >
                <CarouselComponent networkBiologyData={diseaseData} />
              </Collapse.Panel>
            ))}
          </Collapse>
        ) : (
          <div className="h-[70vh] flex justify-center items-center">
            <Empty description="No data available" />
          </div>
        )}
      </div>
    </section>
  );
};

export default NetworkBiology;
