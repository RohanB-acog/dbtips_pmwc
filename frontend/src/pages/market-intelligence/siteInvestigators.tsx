import { useState, useEffect, useMemo } from "react";
import { Tooltip } from "antd";
import { PhoneOutlined, MailOutlined } from "@ant-design/icons";
import { useQuery } from "react-query";
import { fetchData } from "../../utils/fetchData";
import LoadingButton from "../../components/loading";
import { Empty,Select } from "antd";
import { capitalizeFirstLetter } from "../../utils/helper";
import parse from 'html-react-parser';
import Table from "../../components/testTable";
const { Option } = Select;
const Name = (name,phone,email) => {
  return (
    <div>
      {name}
      {phone&& (
        <span>
          <Tooltip title={phone}>
            <PhoneOutlined className="ml-1 " />
          </Tooltip>
        </span>
      )}
      {email && (
        <span>
          <Tooltip title={email}>
            <MailOutlined className="ml-2" />
          </Tooltip>
        </span>
      )}
    </div>
  );
};
const IdLink=({value})=>{
    return (
      <a href={`https://clinicaltrials.gov/study/${value}`} target="_blank" rel="noopener noreferrer">
              {value}
          </a>
    )
  }
  const convertToArray = (data)=>Object.entries(data).map(([disease, nctData]) => {
    return Object.entries(nctData).map(([nctId, trials]) => {
      return trials.map(trial => ({
        Disease: disease,
        nctId,
        name: trial.name,
        affiliation: parse(trial.affiliation),
        location: trial.location,
       contact: trial.contact,
        type: trial.type
      }));
    }).flat();
  }).flat();

const SiteInvestigators = ({ indications }) => {
  const [selectedDisease, setSelectedDisease] = useState(indications);
  const [rowData, setRowData] = useState([]);
  const payload = { diseases: indications };
  const columns = [
    {
        field:"Disease",
        headerName: "Disease",
        cellRenderer: (params) => { 
          return capitalizeFirstLetter(params.value);
        }
        
        
      },
    {
      headerName: "Location",
      field: "location",
      
      flex: 1.5,
    },
    {
      headerName: "Trial ID",
      field: "nctId",
    
      cellRenderer: IdLink,
    },
    {
      headerName: "Principal investigator",
      field: "name",
      
      cellRenderer: params=>Name(params.value,params.data.phone,params.data.email),
    },
    {
      headerName: "Affiliation",
      field: "affiliation",
          flex: 1.5,
    },

    {
      headerName: "Site contact",
      field: "contact",
     
      cellRenderer: params => Name(params.value.name,params.value.phone,params.value.email),
    },
  ];
  const {
    data: siteInvestigatorsData,
    error: siteInvestigatorsError,
    isLoading: siteInvestigatorsLoading,
  } = useQuery(
    ["siteInvestigatorsDetails", payload],
    () => fetchData(payload, "/market-intelligence/kol/"),
    {
      enabled: !!indications.length,
      refetchOnWindowFocus: false,
      refetchOnMount: false,
      staleTime: 5 * 60 * 1000,
    }
  );
  useEffect(() => {
    setSelectedDisease(indications);
   } , [indications]);
  const processedData=useMemo(()=>{
    if(siteInvestigatorsData){
      return convertToArray(siteInvestigatorsData);
    }
    return [];
  }
    ,[siteInvestigatorsData])
    useEffect(() => {
        if (processedData) {
        //   const processedData = convertToArray(influencersData);
          const filteredData = selectedDisease === "All" 
            ? processedData 
            : processedData.filter((row) =>
              selectedDisease.some(indication => 
                indication.toLowerCase() === row.Disease.toLowerCase()
              )
              );
          setRowData(filteredData);
        }
      }, [selectedDisease, siteInvestigatorsData]);
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
  return <div id="siteInvetigators">
    <h2 className="text-xl subHeading font-semibold mb-3 mt-2">
        Site Investigators
      </h2>

    {siteInvestigatorsLoading && <LoadingButton />}
    {siteInvestigatorsError && !siteInvestigatorsLoading && (
      <div className="mt-4 h-[50vh]  flex items-center justify-center">
        <Empty description={`${siteInvestigatorsError}`} />
      </div>
    )}
    {!siteInvestigatorsLoading && !siteInvestigatorsError && siteInvestigatorsData && (
        <div>

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
      <div className={`ag-theme-quartz mt-4 mb-10  `}>
        <Table
        
          columnDefs={columns}
          rowData={rowData}
            


        />
      </div>
      </div>
    )}

  </div>;
};

export default SiteInvestigators;
