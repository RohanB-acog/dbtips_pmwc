import { useEffect, useState, useMemo } from "react";
import { AgGridReact } from "ag-grid-react";
import { Empty, Select, message, Tooltip, Button } from "antd";
import LoadingButton from "../../components/loading";
import parse from "html-react-parser";
import { fetchData } from "../../utils/fetchData";
import { useQuery } from "react-query";
import { useLocation } from "react-router-dom";
import { parseQueryParams } from "../../utils/parseUrlParams";
// import * as XLSX from "xlsx";
// import NetworkBiology from "./networkBiology";
import ModelStudies from "./mouseStudies";
// import SelectedLiterature from "./selectedLiterature";
// import Genomics from "./functionalGenomics"
import { capitalizeFirstLetter } from "../../utils/helper";
import { useChatStore } from "chatbot-component";
import BotIcon from "../../assets/bot.svg?react";
import { preprocessLiteratureData } from "../../utils/llmUtils";
const { Option } = Select;

function convertToArray(data) {
  const result = [];
  Object.keys(data).forEach((disease) => {
    console.log("disease inside convert array function", disease);
    data[disease]["literature"].forEach((record) => {
      result.push({
        ...record,
        Disease: capitalizeFirstLetter(disease), // Add the disease key
      });
    });
  });
  return result;
}

const Evidence = () => {
  const location = useLocation();
  const [indications, setIndications] = useState([]);
  const [target, setTarget] = useState("");
  const [selectedIndication, setSelectedIndication] = useState(indications);
  const [selectedLiterature, setSelectedLiterature] = useState([]);
  const { register, invoke } = useChatStore();

  const payload = {
    diseases: indications,
    target: target,
  };

  const {
    data: evidenceLiteratureData,
    error: evidenceLiteratureError,
    isLoading: evidenceLiteratureLoading,
    isFetching: evidenceLiteratureFetching,
  } = useQuery(
    ["evidenceLiterature", payload],
    () => fetchData(payload, "/evidence/target-literature/"),
    {
      enabled: !!indications.length,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
      refetchOnMount: false,
    }
  );
  useEffect(() => {
    setSelectedIndication(indications);
  }, [indications]);
  const processedData = useMemo(() => {
    if (evidenceLiteratureData) {
      return convertToArray(evidenceLiteratureData);
    }
    return [];
  }, [evidenceLiteratureData]);
  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const { indications, target } = parseQueryParams(queryParams);
    setIndications(indications);
    setTarget(target?.split("(")[0]);
  }, [location]);

  const rowData = useMemo(() => {
    if (processedData.length > 0) {
      return selectedIndication.length === indications.length
        ? processedData
        : processedData.filter((row) =>
            selectedIndication.some(
              (indication) =>
                indication.toLowerCase() === row.Disease.toLowerCase()
            )
          );
    }
    return [];
  }, [processedData, selectedIndication]);

  const handleSelect = (value: string[]) => {
    if (value.includes("All")) {
      // If "All" is selected, select all diseases but don't include "All" in display
      setSelectedIndication(indications);
    } else if (
      selectedIndication.length === indications.length &&
      value.length < indications.length
    ) {
      // If coming from "all selected" state and deselecting, just use the new selection
      setSelectedIndication(value);
    } else {
      // Normal selection behavior
      setSelectedIndication(value);
    }
  };

  const onSelectionChanged = (event: any) => {
    const selectedNodes = event.api.getSelectedNodes();
    const selectedCount = selectedNodes.length;

    if (selectedCount > 10) {
      // Deselect the latest selection
      const lastSelectedNode = selectedNodes[selectedNodes.length - 1];
      lastSelectedNode.setSelected(false);
      message.warning("You can select a maximum of 10 rows.");
    } else {
      const selectedData = selectedNodes.map((node: any) => node.data);
      setSelectedLiterature(selectedData);
    }
  };
  const showLoading = evidenceLiteratureLoading || evidenceLiteratureFetching;

  useEffect(() => {
    if (selectedLiterature?.length > 0) {
      const llmData = preprocessLiteratureData(selectedLiterature);
      const urls = selectedLiterature.map((data: any) => data.PubMedLink);
      const diseases = [
        ...new Set(selectedLiterature.map((data: any) => data.Disease)),
      ];
      // console.log(llmData);
      register("literature", {
        urls: urls,
        target: target,
        diseases: diseases,
        data: llmData,
      });
    }

    // return () => {
    // 	unregister('pipeline_indications');
    // };
  }, [selectedLiterature]);

  const handleLLMCall = () => {
    invoke("literature", { send: false });
  };

  return (
    <div className=" mt-8  ">
      <section id="literature-evidence " className="px-[5vw]">
        <div className="flex space-x-5 items-center">
          <h1 className="text-3xl font-semibold">Literature repository</h1>
          <Tooltip title="Please select articles to ask LLM">
            <Button
              type="default" // This will give it a simple outline
              onClick={handleLLMCall}
              className="w-18 h-8 text-blue-800 text-sm flex items-center"
            >
              <BotIcon width={16} height={16} fill="#d50f67" />
              <span>Ask LLM</span>
            </Button>
          </Tooltip>
        </div>
        <p className="my-2  font-medium ">
          This section offers a curated collection of recent research articles
          highlighting the target's role in the disease.
        </p>

        {/* <SelectedLiterature selectedIndication={selectedIndication} indications={indications}/> */}
        {/* <h2 className='subHeading text-xl mt-10 font-semibold  mb-4'>
					{' '}
					Review repository
				</h2> */}

        {showLoading && <LoadingButton />}

        {evidenceLiteratureError &&
          !evidenceLiteratureLoading &&
          !evidenceLiteratureData && (
            <div className="h-[40vh] flex items-center justify-center">
              <Empty description={String(evidenceLiteratureError)} />
            </div>
          )}
        {!showLoading && !evidenceLiteratureError && evidenceLiteratureData && (
          <div className="flex mb-3">
            <div>
              <span className="mt-10 mr-1">Disease: </span>
              <span>
                <Select
                  style={{ width: 300 }}
                  onChange={handleSelect}
                  showSearch={false}
                  value={selectedIndication}
                  mode="multiple"
                  maxTagCount="responsive"
                  disabled={evidenceLiteratureLoading}
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
        )}

        {!showLoading && !evidenceLiteratureError && rowData.length > 0 && (
          <>
            <div className="ag-theme-quartz h-[80vh] ">
              <AgGridReact
                defaultColDef={{
                  flex: 1,
                  filter: true,
                  sortable: true,
                  floatingFilter: true,
                  headerClass: "font-semibold",
                  autoHeight: true,
                  wrapText: true,
                  cellStyle: { whiteSpace: "normal", lineHeight: "20px" },
                }}
                columnDefs={[
                  {
                    headerName: "",
                    checkboxSelection: true,
                    filter: false,
                  },
                  {
                    field: "Disease",
                    headerName: "Disease",
                    flex: 3,
                  },
                  { field: "Year", flex: 1.3 },
                  {
                    field: "Qualifers",
                    headerName: "Category",
                    flex: 3,
                    valueFormatter: (params) => {
                      if (params.value) {
                        return params.value.join(", ");
                      }
                      return "";
                    },
                  },
                  {
                    field: "Title",
                    headerName: "Title",
                    flex: 10,
                    cellRenderer: (params) => {
                      return (
                        <a href={params.data.PubMedLink} target="_blank">
                          {parse(params.value)}
                        </a>
                      );
                    },
                  },
                  {
										headerName: 'Authors',
										field:"authors",
										cellRenderer: (params) => {
										  const authors = params.value;
										  
										  if (!authors || authors.length === 0) {
											return "";
										  }
										  
										  // Show all authors if there are 4 or fewer
										  if (authors.length <= 4) {
											return (
											<div>
											   {authors.join(', ')}
											</div>
											);
										  }
										  
										  // For more than 4 authors, show first 3 and last one with tooltip
										  const displayText = ` ${authors.slice(0, 3).join(', ')}, .... , ${authors[authors.length - 1]}`;
										  const allAuthors = ` ${authors.join(', ')}`;
										  
										  return (
											<Tooltip title={allAuthors} placement="topLeft">
											<div className="truncated-authors">
											  {displayText}
											</div>
											</Tooltip>
										  );
										  },
										flex:3
									  },
									  {
										field:"citedby",
										headerName:"Cited by",
										flex:2
									  }
                ]}
                rowData={rowData}
                rowSelection="multiple"
                pagination={true}
                rowMultiSelectWithClick={true}
                onSelectionChanged={onSelectionChanged}
				enableRangeSelection={true}
				enableCellTextSelection={true}
              />
            </div>
          </>
        )}

        {!evidenceLiteratureLoading &&
          !evidenceLiteratureError &&
          evidenceLiteratureData &&
          rowData.length === 0 && (
            <div className="h-[40vh] flex items-center justify-center">
              <Empty description="No  data available" />
            </div>
          )}

        {/* <AskLLM target={target} indications={indications} /> */}
      </section>

      <ModelStudies target={target} />
    </div>
  );
};

export default Evidence;
