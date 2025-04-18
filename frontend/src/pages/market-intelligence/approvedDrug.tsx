import { useState, useMemo, useEffect } from "react";
import { Empty, Select } from "antd";
import LoadingButton from "../../components/loading";
import Table from "../../components/testTable";
import { capitalizeFirstLetter } from "../../utils/helper";

const { Option } = Select;

const ApprovedDrug = ({
  approvedDrugData,
  loading,
  error,
  indications,
  isFetchingData,
}) => {
	const [selectedDisease, setSelectedDisease] = useState(indications);

  const filteredData = useMemo(() => {
    if (!approvedDrugData) return [];

    const filtered =
  selectedDisease.includes("All")
    ? approvedDrugData.filter((data) => data.ApprovalStatus === "Approved")
    : approvedDrugData.filter(
        (data) =>
          selectedDisease.some(
            (disease) => disease.toLowerCase() === data.Disease.toLowerCase()
          ) && data.ApprovalStatus === "Approved"
      );


    // Unique data filtering
    const uniqueKeys = new Set(
      filtered.map((item) => `${item.Target}-${item.Disease}-${item.Drug}`)
    );

    return Array.from(uniqueKeys).map(
      (key) =>
        filtered.find(
          (item) => `${item.Target}-${item.Disease}-${item.Drug}` === key
        )!
    );
  }, [selectedDisease, approvedDrugData]);
  useEffect(() => {
    setSelectedDisease(indications);
   } , [indications]);
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
    
  const showLoading = isFetchingData || loading;

  return (
    <section id="approvedDrug" className="px-[5vw]">
      <h1 className="text-3xl font-semibold mb-4">Approved Drugs</h1>
      <p className="mt-2 font-medium mb-2">
        List of approved drugs for all the indications
      </p>
      <span>Disease: </span>
      <Select
        showSearch
        style={{ width: 500 }}
        onChange={handleDiseaseChange}
        placeholder="Select Disease"
        value={selectedDisease}
        mode="multiple"
        maxTagCount="responsive"
      >
        <Option value="All">All</Option>
        {indications.map((indication) => (
          <Option key={indication} value={indication}>
            {indication}
          </Option>
        ))}
      </Select>
      {showLoading && <LoadingButton />}
      {error && !showLoading && (
        <div className="ag-theme-quartz mt-4 h-[50vh] max-h-[280px] flex items-center justify-center">
          <Empty description={`${error}`} />
        </div>
      )}
      {!showLoading && !error && filteredData && (
        <div className=" mt-4 mb-10">
          <Table
            columnDefs={[
              {
                field: "Disease",
                cellRenderer: (params) => capitalizeFirstLetter(params.value),
              },
              { field: "Target" },
              { field: "Drug" },
            ]}
            rowData={filteredData}
          />
        </div>
      )}

      {/* {renderContent()} */}
    </section>
  );
};

export default ApprovedDrug;
