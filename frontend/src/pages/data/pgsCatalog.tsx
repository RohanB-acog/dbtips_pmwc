import { useState, useMemo, useEffect } from "react";
import { fetchData } from "../../utils/fetchData";
import { capitalizeFirstLetter } from "../../utils/helper";
import { Empty, Select } from "antd";
import { AgGridReact } from "ag-grid-react";
import parse from "html-react-parser";
import { useQuery } from "react-query";
import LoadingButton from "../../components/loading";
import PieChart from "../../components/pieChart";
const { Option } = Select;
import { FileText } from "lucide-react";
function convertToArray(data) {
  const result = [];
  Object.keys(data).forEach((disease) => {
    data[disease].forEach((record) => {
      result.push({
        ...record,
        disease: capitalizeFirstLetter(disease), // Add the disease key
      });
    });
  });
  return result;
}
const GwasRenderer = ({ value }) => {
  return (
    <div>
      <PieChart
        chartData={value?.gwas}
        symbol={"G"}
        heading="G- Source of Variant Associations (GWAS)"
      />
    </div>
  );
};
const DevRenderer = ({ value }) => {
  return (
    <div>
      <PieChart
        chartData={value?.dev}
        symbol={"D"}
        heading="D - Score Development/Training"
      />
    </div>
  );
};
const evalRenderer = ({ value }) => {
  return (
    <div>
      <PieChart
        chartData={value?.eval}
        symbol={"E"}
        heading="E - PGS Evaluation"
      />
    </div>
  );
};

const PgsCatalog = ({ indications }) => {
  const [selectedDisease, setSelectedDisease] = useState(indications);
  const payload = {
    diseases: indications,
  };

  const {
    data: pgsCatalogData,
    error: pgsCatalogError,
    isLoading,
  } = useQuery(
    ["pgsCatalog", payload],
    () => fetchData(payload, "/genomics/pgscatalog"),
    {
      enabled: !!indications.length,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
      refetchOnMount: false,
    }
  );
  useEffect(() => {
    setSelectedDisease(indications);
  }, [indications]);

  const processedData = useMemo(() => {
    if (pgsCatalogData) {
      return convertToArray(pgsCatalogData);
    }
    return [];
  }, [pgsCatalogData]);
  console.log("processedData", processedData);
  const rowData = useMemo(() => {
    if (processedData.length > 0) {
      // If all diseases are selected (length matches total indications)
      return selectedDisease.length === indications.length
        ? processedData
        : processedData.filter((row) =>
            selectedDisease.some(
              (indication) =>
                indication?.toLowerCase() === row.disease?.toLowerCase()
            )
          );
    }
    return [];
  }, [processedData, selectedDisease]);
  const columns = [
    {
      field: "disease",
      headerName: "Disease",
    },
    {
      field: "PGS ID",
      valueGetter: (params) => {
        return `
        <div>
                <span>${params.data["PGS ID"]}</span>
                <p class ="text-xs" >(${params.data["PGS Name"]})</p>
            </div>
        `;
      },

      headerName: "Polygenic Score ID & Name",
      cellRenderer: (params) => {
        return parse(params.value);
      },
    },
    {
      field: "PGS Publication ID",
      headerName: "PGS Publication ID (PGP)",
      valueGetter: (params) => {
        return `
        <div>
                <span>${params.data["PGS Publication ID"]}</span>
                <p class ="text-xs">>>${params.data["PGS Publication First Author"]} et al. ${params.data["PGS Publication Journal"]} (${params.data["PGS Publication Year"]})</p>
            </div>
        `;
      },
      cellRenderer: (params) => {
        return parse(params.value);
      },
      minWidth: 300,
    },
    {
      field: "PGS Reported Trait",
      headerName: "Reported trait",
    },
    {
      field: "PGS Number of Variants",
      headerName: "Number of Variants",
    },
    {
      headerName: "Ancestry distribution",
      headerClass: "ag-header-cell-center", // Add this line
      children: [
        {
          headerName: "GWAS",
          field: "PGS Ancestry Distribution",
          cellRenderer: GwasRenderer,
          floatingFilter: false,
          filter: false,
          maxWidth: 70,
          sortable: false,
          headerClass: "ag-header-cell-center", // Add this to center child headers too
        },
        {
          headerName: "Dev",
          cellRenderer: DevRenderer,
          field: "PGS Ancestry Distribution",
          floatingFilter: false,
          filter: false,
          maxWidth: 70,
          sortable: false,
          headerClass: "ag-header-cell-center",
        },
        {
          headerName: "Eval",
          field: "PGS Ancestry Distribution",
          cellRenderer: evalRenderer,
          floatingFilter: false,
          filter: false,
          maxWidth: 70,
          sortable: false,
          headerClass: "ag-header-cell-center",
        },
      ],
    },
    {
      field: "PGS Scoring File",
      headerName: "Scoring File (FTP Link)",
      maxWidth: 140,
      floatingFilter: false,
      filter: false,
      cellRenderer: (params) => {
        return (
          <a href={params.value} target="_blank" rel="noreferrer">
            <FileText size={35} />
          </a>
        );
      },
      cellStyle: {
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }, // Add the centering styles
    },
  ];
  const handleDiseaseChange = (value: string[]) => {
    if (value.includes("All")) {
      // If "All" is selected, select all diseases but don't include "All" in display
      setSelectedDisease(indications);
    } else if (
      selectedDisease.length === indications.length &&
      value.length < indications.length
    ) {
      // If coming from "all selected" state and deselecting, just use the new selection
      setSelectedDisease(value);
    } else {
      // Normal selection behavior
      setSelectedDisease(value);
    }
  };
  return (
    <div id="pgsCatalog" className="mt-7">
      <h2 className="text-xl subHeading font-semibold mb-3  ">
        Polygenic risk scores
      </h2>
      <p className="my-1">
        Quantifies an individual’s genetic susceptibility to{" "}
        {indications.join(", ")} based on multiple risk variants.
      </p>
      {isLoading && <LoadingButton />}
      {pgsCatalogError && (
        <div>
          <Empty description={`${pgsCatalogError}`} />
        </div>
      )}
      {pgsCatalogData && (
        <div>
          <div className="flex mb-3">
            <div>
              <span className="mt-10 mr-1">Disease: </span>
              <span>
                <Select
                  style={{ width: 500 }}
                  // onChange={handleSelect}
                  mode="multiple"
                  maxTagCount="responsive"
                  onChange={handleDiseaseChange}
                  value={selectedDisease}
                  disabled={isLoading}
                  showSearch={false}
                >
                  <Option value="All">All</Option>
                  {indications.map((indication) => (
                    <Option key={indication} value={indication}>
                      {indication}
                    </Option>
                  ))}
                </Select>
              </span>
            </div>
          </div>
          <div className="ag-theme-quartz h-[70vh]">
            <AgGridReact
              defaultColDef={{
                sortable: true,
                filter: true,
                resizable: true,
                flex: 1,
                floatingFilter: true,
                cellStyle: {
                  whiteSpace: "normal",
                  lineHeight: "20px",
                },
                wrapHeaderText: true,
                autoHeight: true,
                wrapText: true,
              }}
              columnDefs={columns}
              rowData={rowData}
              pagination={true}
              paginationPageSize={10}
              enableCellTextSelection={true}
              enableRangeSelection={true}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default PgsCatalog;
