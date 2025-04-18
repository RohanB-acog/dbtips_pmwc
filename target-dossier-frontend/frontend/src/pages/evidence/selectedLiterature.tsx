// import { AgGridReact } from "ag-grid-react";
import parse from "html-react-parser";
import {  Empty } from "antd";
import Table from "../../components/testTable"
import { fetchData } from "../../utils/fetchData";
import { useQuery } from "react-query";
import LoadingButton from "../../components/loading";
import {  useMemo } from "react";
import { capitalizeFirstLetter } from "../../utils/helper";

function convertToArray(data) {
  const result = [];
  console.log("data outside convert array function", data);
  Object.keys(data).forEach((disease) => {
    console.log("disease inside convert array function", disease);
    data[disease]?.forEach((record) => {
      result.push({
        ...record,
        Disease:capitalizeFirstLetter(disease), // Add the disease key
      });
    });
  });
  return result;
}

const SelectedLiterature = ({ selectedIndication,indications }) => {
  
  const payload = {
    diseases: indications,
  };
  const {
    data: selectedLiteratureData,
    error: selectedLiteratureError,
    isLoading: selectedLiteratureLoading,
    isFetching: selectedLiteratureFetching,
  } = useQuery(
    ["selectedLiterature", selectedIndication],
    () => fetchData(payload, "/evidence/top-10-literature/"),
    {
      enabled: !!indications.length,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
      refetchOnMount: false,
     
    }
  );

  const processedData = useMemo(() => {
    if (selectedLiteratureData) {
      return convertToArray(selectedLiteratureData);
    }
    return [];
  },  [selectedLiteratureData]);



  const rowData = useMemo(() => {
    if (processedData.length > 0) {
      return selectedIndication === "All"
        ? processedData
        : processedData.filter(
            (row) =>
              row.Disease.toLowerCase() === selectedIndication.toLowerCase()
          );
    }
    return [];
  }
  ,[processedData,selectedIndication]);
    const showLoading = selectedLiteratureFetching || selectedLiteratureLoading;
  return (
    <div>
      <h2 className="subHeading text-xl font-semibold mt-4">
      Select reviews

      </h2>

      {showLoading && <LoadingButton />}
      {selectedLiteratureError  && !selectedLiteratureData && <Empty description="Error" />}
        { selectedLiteratureData && !showLoading && !selectedLiteratureError&&
      <div className="ag-theme-quartz mt-4  ">
        <Table
          
          columnDefs={[
            {
              field: "Disease",
              headerName: "Disease",
              flex: 3,
            },
            { field: "year", headerName: "Year",flex:2 },

            {
              field: "title_text",
              headerName: "Title",
              flex: 10,
              cellRenderer: (params) => {
                return (
                  <a href={params.data.title_url} target="_blank">
                    {parse(params.value)}
                  </a>
                );
              },
            },
          ]}
          rowData={rowData}
          maxRows={ rowData.length > 10 ? 10 : rowData.length}
          rowHeight={30}
       />
      </div>}
      
    </div>
  );
};

export default SelectedLiterature;
