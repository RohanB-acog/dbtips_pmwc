import {useEffect, useState,useMemo} from 'react'
import { AgGridReact } from "ag-grid-react";
import { useQuery } from "react-query";
import { Empty,Select } from "antd";
import { fetchData } from "../../utils/fetchData";
import { capitalizeFirstLetter } from "../../utils/helper";
import LoadingButton from "../../components/loading";
const {Option} =Select
function convertToArray(data) {
  const result = [];
  Object.keys(data).forEach((disease) => {
    data[disease].forEach((record) => {
      result.push({
        ...record,
        pubDate: record["Pub. date"],
        disease: capitalizeFirstLetter(disease), // Add the disease key
      });
    });
  });
  return result;
}
const AssociatePlot = ({indications}) => {
  const [selectedDisease, setSelectedDisease] = useState(indications);
  const payload = {
    diseases: indications,
  };
  useEffect(() => {
    setSelectedDisease(indications);
  }, [indications]);
  const {
    data: gwasStudiesData,
    error: gwasStudiesError,
    isLoading,
  } = useQuery(
    ["gwas-studies", payload],
    () => fetchData(payload, "/genomics/gwas-studies"),
    {
      enabled: !!indications.length,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
      refetchOnMount: false,
    }
  );
  const processedData = useMemo(() => {
    if (gwasStudiesData) {
      return convertToArray(gwasStudiesData);
    }
    return [];
  }, [gwasStudiesData,]);

  const rowData = useMemo(() => {
    if (processedData.length > 0) {
      // If all diseases are selected (length matches total indications)
      return selectedDisease.length === indications.length
        ? processedData
        : processedData.filter((row) =>
            selectedDisease.some(indication => 
              indication?.toLowerCase() === row.disease?.toLowerCase()
            )
          );
    }
    return [];
  }, [processedData, selectedDisease]);
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
    <div className='my-5' id ="gwas-studies">
      				<h2 className='text-xl subHeading font-semibold mb-3 mt-2 '>GWAS summary plot</h2>
          <div className='mt-4'>
          </div>       
          <h2 className='text-lg subHeading font-semibold mb-3 mt-4'>GWAS studies</h2>  
          <p className='my-1 font-medium'>Identify genetic variants linked to {indications.join(", ")} by scanning the genomes of large populations.
          </p> 
          {isLoading && <LoadingButton /> }
          {gwasStudiesError && 
          <div>
            <Empty description={`${gwasStudiesError}`} />
          </div>
          }        
          {
            !isLoading && !gwasStudiesError && gwasStudiesData && (

              <div className='mt-4'>
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
                <div className='ag-theme-quartz h-[70vh]' >
                  <AgGridReact
                    rowData={rowData}
                    defaultColDef={{
                      sortable: true,
                      filter: true,
                      resizable: true,
                      minWidth:150,
                      floatingFilter: true,
                      cellStyle: {
                        whiteSpace: "normal",
                        lineHeight: "20px",
                      },
                      wrapHeaderText: true,
                      autoHeaderHeight: true,
                      autoHeight: true,
                      wrapText: true,
                      

                    }}
                    pagination={true}
                    paginationPageSize={20}
                    columnDefs={[
                      {
                        headerName: "Disease",
                        field: "disease",
                        
                      },
                      {
                       
                        field: "First author",
                       
                      },
                      {
                        field:"Study accession"
                      },
                      {
                         field:"pubDate",
                         filter: "agDateColumnFilter",
                         headerName: "Pub. Date ",
                         flex:2
                      },
                      {
                        field:"Journal"
                      },
                      {
                        field:"Title",
                        minWidth:200
                      },
                      {
                        field:"Reported trait"
                      },
                      {
                        field: "Trait(s)",
                        
                        
                      },
                      {
                        field:"Discovery sample ancestry"
                      },
                      {
                        field:"Replication sample ancestry",
                        flex:2
                      },
                     
                      {
                        field:"Association count",
                        maxWidth:100,
                        cellRenderer: (params) => {
                          if(params.value){
                            return params.value
                          }
                          else return ""
                        }
                      },
                      {
                        field:"Summary statistics",
                        cellRenderer: (params) => {
                          if(params.value!=="NA"){
                            return (  
                              <a href={params.value} target="_blank">FTP download</a>)}
                            else return "Not available"}
                              
                      }
                      
                    ]}
                    enableCellTextSelection={true}
                    enableRangeSelection={true}
                    
                  />
                </div>
              </div>
            )
          }
          
    </div>
  )
}

export default AssociatePlot