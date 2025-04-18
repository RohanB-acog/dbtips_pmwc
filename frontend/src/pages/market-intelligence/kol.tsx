import { Select, Empty } from "antd";
import { useState, useEffect} from "react";
import { useQuery } from "react-query";
import { fetchData } from "../../utils/fetchData";
import LoadingButton from "../../components/loading";
import { capitalizeFirstLetter } from "../../utils/helper";
import SiteInvestigators from "./siteInvestigators";
import Table from "../../components/testTable"
const { Option } = Select;

function convertToArray(data) {
  const result = [];
  Object.keys(data).forEach((disease) => {
    data[disease].forEach((record) => {
      result.push({
        
        Disease: disease, // Add the disease key
        name: record.name,
        expertise: record.expertise,
        affiliation: record.affiliation,
        notable_talks: {
          text: record?.notable_talks?.text || '',
          url: record?.notable_talks?.url || '',
        },
        publications: {
          text: record?.publications ? "View Publication" : '',
          url: record?.publications?.length ? record.publications[0] : '',
        },
      });
    });
  });
  return result;
}

const TrialIDLink = ({ value }) => {
  return (
    <a href={`${value.url}`} target="_blank" rel="noopener noreferrer">
      {value.text}
    </a>
  );
};


const Kol = ({ indications }) => {
	const [selectedDisease, setSelectedDisease] = useState(indications);
  const [rowData, setRowData] = useState([]);
 
  const payload = { diseases: indications };

  const {
    data: influencersData,
    error: influencerError,
    isLoading: influencerLoading,
  } = useQuery(["influencerDetails", payload], () =>
    fetchData(payload, "/market-intelligence/key-influencers/"),
    {
      enabled: !!indications.length,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
      refetchOnMount: false,
    }
  );

  // Effect to automatically select the first disease when data is loaded

  const columnDefs = [
    {
      field:"Disease",
      headerName: "Disease",
      cellRenderer: (params) => { 
        return capitalizeFirstLetter(params.value);
      }
      
      
    },
    {
      headerName: "Name",
      field: "name",
      sortable: true,
      filter: true,
      flex: 1,
    },
    {
      headerName: "Affiliation",
      field: "affiliation",
      sortable: true,
      filter: true,
      flex: 1,
    },
    {
      headerName: "Expertise",
      field: "expertise",
      sortable: true,
      filter: true,
      flex: 1.5,
    },
    {
      headerName: "Notable talks",
      field: "notable_talks",
      cellRenderer: TrialIDLink,
      flex: 1,
    },
    {
      headerName: "Publications",
      field: "publications",
      cellRenderer: TrialIDLink,
      flex: 1,
    },
  ];
  
  useEffect(() => {
   setSelectedDisease(indications);
  } , [indications]);
  useEffect(() => {
    if (influencersData && selectedDisease) {
      const processedData = convertToArray(influencersData);
      const filteredData = selectedDisease === "All" 
        ? processedData 
        : processedData.filter((row) =>
          selectedDisease.some(indication => 
            indication.toLowerCase() === row.Disease.toLowerCase()
          )
          );
      setRowData(filteredData);
    }
  }, [selectedDisease, influencersData]);
  const handleDiseaseChange = (value: string[]) => {
		if (value.includes('All')) {
		  // If "All" is selected, select all diseases but don't include "All" in display
		  setSelectedDisease(indications);
		} else if (selectedDisease.length === indications.length && value.length < indications.length) {
		  // If coming from "all selected" state and deselecting, just use the new selection
		  setSelectedDisease(value);
		} else {
		  // Normal selection behavior
		  setSelectedDisease(value);
		}
	  }; 

  return (
    <article >
      <h1 className="text-3xl font-semibold mb-3">Opinion leaders</h1>
      <p className="mt-1  font-medium mb-2">
      Opinion leaders are experts driving innovation in disease research, bridging basic science and clinical application to advance diagnostics and therapies.      </p>
      <SiteInvestigators indications={indications}/>
      <h2 className="text-xl subHeading font-semibold mb-3 mt-2" id="kol">
        Key influential leaders
      </h2>
      {influencerLoading && <LoadingButton />}
      {influencerError && (
        <div className="ag-theme-quartz mt-4 h-[80vh] max-h-[280px] flex items-center justify-center">
          <Empty />
        </div>
      )}
      {!influencerError && !influencerLoading && (
        <>
         <div className="flex justify-between mb-3">
        <div>
          <span>Disease: </span>
          <Select
            value={selectedDisease}
            placeholder="Select a disease"
            onChange={handleDiseaseChange}
            style={{ width: 500 }}
            mode="multiple"
            maxTagCount="responsive"
            
            
          >
            <Option key="All" value="All">
              All
            </Option>
            {indications.map((indication) => (
                  <Option key={indication} value={indication}>
                    {indication}
                  </Option>
                ))}
          </Select>
        </div>
        {/* <Button onClick={onExportClick} disabled={!rowData} type="primary" icon={<FileExcelOutlined   className=" align-middle  text-xl" />}>
         Export
        </Button> */}

      </div>

          <div
            className=" w-full  "
          >
            <Table
              columnDefs={columnDefs}
             
              rowData={rowData}
            />
          </div>
        </>
      )}
      {/* <h2 className="text-xl subHeading font-semibold mb-3 mt-8">
        Key researchers
      </h2>
      <div className="flex justify-between">
        <div>
          <span>Disease: </span>
          <Select
            value={selectedDisease}
            placeholder="Select a disease"
            disabled
            onChange={handleSelectChange}
            style={{ width: 300, marginBottom: 20 }}
            options={Object.keys(influencersData || {}).map((key) => ({
              label: key,
              value: key,
            }))}
          />
        </div>
      </div>
      <div className="ag-theme-quartz" style={{ height: 350, width: "100%" }}>
        <AgGridReact
          columnDefs={[]}
          defaultColDef={{
            minWidth: 150,
            flex: 1,
            filter: true,
            sortable: true,
            floatingFilter: true,
            headerClass: "font-semibold",
            autoHeight: true,
            wrapText: true,
            cellStyle: { whiteSpace: "normal", lineHeight: "20px" },
          }}
          noRowsOverlayComponent={CustomNoRowsOverlay}
          rowData={[]}
          pagination={true}
          paginationPageSize={20}
        />
      </div> */}
    </article>
  );
};

export default Kol;
