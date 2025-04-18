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
  target
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
      filtered.map((item) => `${item.Disease}-${item.Drug.toLowerCase()}`)
    );

    return Array.from(uniqueKeys).map(
      (key) =>
        filtered.find(
          (item) => `${item.Disease}-${item.Drug.toLowerCase()}` === key
        )!
    );
  }, [selectedDisease, approvedDrugData]);

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
  useEffect(() => {
    setSelectedDisease(indications);
   } , [indications]);
  const showLoading = isFetchingData || loading;

  return (
    <section id="approvedDrug" className="px-[5vw]">
      <h1 className="text-3xl font-semibold mb-4">Approved drugs</h1>
      <p className="mt-2 font-medium mb-2">
      This section lists drugs targeting {target} that have been approved by regulatory authorities for one or more diseases.
      </p>
     { approvedDrugData?.length>0 &&
      <div>
      <span>Disease: </span>
      <Select
        showSearch={false}
        style={{ width: 300 }}
        onChange={handleDiseaseChange}
        mode="multiple"
        maxTagCount="responsive"
        placeholder="Select Disease"
        value={selectedDisease}
      >
        <Option value="All">All</Option>
        {indications.map((indication) => (
          <Option key={indication} value={indication}>
            {indication}
          </Option>
        ))}
      </Select>
      </div>
      }
      {showLoading && <LoadingButton />}
      {error && !showLoading && (
        <div className="ag-theme-quartz mt-4 h-[50vh] max-h-[280px] flex items-center justify-center">
          <Empty description={String(error)} />
        </div>
      )}
      {!showLoading && !error && filteredData && (
        <div className="ag-theme-quartz mt-4 mb-10">
          <Table
            columnDefs={[
              {
                field: "Disease",
                cellRenderer: (params) => capitalizeFirstLetter(params.value),
              },
              // { field: "Target" },
              { field: "Drug" },
            ]}
            rowData={filteredData}
            maxRows={filteredData.length > 10 ? 10 : filteredData.length}
          />
        </div>
      )}

      {/* {renderContent()} */}
    </section>
  );
};

export default ApprovedDrug;
