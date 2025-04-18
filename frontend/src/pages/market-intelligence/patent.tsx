import { useState, useEffect } from "react";
import { AgGridReact } from "ag-grid-react";
import { useQuery } from "react-query";
import { fetchData } from "../../utils/fetchData";
import LoadingButton from "../../components/loading";
import { Empty, Select } from "antd";
import countries from "./countries.yaml";

const { Option } = Select;

const PatentLink = (params) => (
  <a href={params.data.pdf} target="_blank" rel="noopener noreferrer">
    {`${params.data.title} (${params.value.split('/')[1]})`}
  </a>
);
const filterParams={
  comparator: (filterDate, cellValue) => {
    const cellDate = new Date(cellValue);
    const cellDateStr = `${cellDate.getFullYear()}-${String(cellDate.getMonth() + 1).padStart(2, '0')}-${String(cellDate.getDate()).padStart(2, '0')}`;
    const filterDateStr = `${filterDate.getFullYear()}-${String(filterDate.getMonth() + 1).padStart(2, '0')}-${String(filterDate.getDate()).padStart(2, '0')}`;
    return cellDateStr.localeCompare(filterDateStr);
  },
  dateFormat: 'yyyy-MM-dd'
}


const valueFormatter = (params) => {
  if (!params.value) return "";
  const date = new Date(params.value);
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
};

const Patent = ({ target, indications }) => {
  const [rowData, setRowData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [countryFilter, setCountryFilter] = useState("US");
  const [statusFilter, setStatusFilter] = useState("ACTIVE");

  const payload = {
    target: target === "TNFRSF4" ? "OX40" : target,
    diseases: indications,
  };

  const { data: patentData, error: patentError, isLoading: patentLoading } = useQuery(
    ["patentDetails", payload],
    () => fetchData(payload, "/evidence/search-patent/"),
    { enabled: !!target && indications.length > 0 }
  );

  useEffect(() => {
    if (patentData) {
      const flattenedData = patentData.results.flatMap((resultGroup) =>
        resultGroup.results.map((patent) => ({
          ...patent,
          disease: resultGroup.disease,
        }))
      );
      setRowData(flattenedData);
    }
  }, [patentData]);

  useEffect(() => {
    const filtered = rowData.filter((item) => {
      const countryMatch = item.country_status?.[countryFilter] === statusFilter;
      // const statusMatch = statusFilter === "UNKNOWN"
      //   ? !item.country_status?.US && !item.country_status?.EP
      //   : item.country_status?.US === statusFilter || item.country_status?.EP === statusFilter;
        
      return countryMatch ;
    });
    console.log(filtered)
    setFilteredData(filtered);
  }, [countryFilter, statusFilter, rowData]);

  const handleCountryChange = (value) => setCountryFilter(value);
  const handleStatusChange = (value) => setStatusFilter(value);

  return (
    <section id="patent" className="px-[5vw] py-20  mt-12">
        <h1 className="text-3xl font-semibold">Patents</h1>
        <p className="italic font-medium mt-2">
        A concise overview of worldwide patents detailing therapeutic innovations related to the target in a related disease context.
        </p>
        <div className="flex gap-3 justify-end  ">
          <div className="flex gap-2">
            <h3 className="mt-1">Patent Office: </h3>
            <Select
              showSearch
              placeholder="Select a country"
              optionFilterProp="children"
              onChange={handleCountryChange}
              style={{ width: 300 }}
              value={countryFilter}
            >
              {countries.countries.map((country) => (
                <Option key={country.code} value={country.code}>
                  {`${country.name} (${country.code})`}
                </Option>
              ))}
            </Select>
          </div>
          <div className="flex gap-2">
            <h3 className="mt-1">Status: </h3>
            <Select
              showSearch
              placeholder="Select a status"
              optionFilterProp="children"
              onChange={handleStatusChange}
              style={{ width: 150 }}
              value={statusFilter}
            >
              <Option key="Active" value="ACTIVE">
                Active
              </Option>
              <Option key="Inactive" value="NOT_ACTIVE">
                Inactive
              </Option>
              <Option key="Unknown" value="UNKNOWN">
                Unknown
              </Option>
            </Select>
          </div>
        </div>
      

      {patentLoading && <LoadingButton />}
      {patentError && (
        <div className="ag-theme-quartz mt-4 h-[80vh] max-h-[280px] flex items-center justify-center">
          <Empty />
        </div>
      )}
      {!patentLoading && !patentError && (
        <div className="ag-theme-quartz mt-4 h-[80vh] max-h-[540px]">
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
              { headerName: "Disease", field: "disease", width: 200 },
              { headerName: "Title", field: "patent_id", cellRenderer: PatentLink, flex:2 },
              { headerName: "Current Assignee", field: "assignee", flex: 2 },
              {
                headerName: "Filing Date",
                field: "filing_date",
                width: 200,
                filter: "agDateColumnFilter",
                filterParams,
                valueFormatter,
              },
              {
                headerName: "Grant Date",
                field: "grant_date",
                width: 200,
                filterParams ,
                valueFormatter,

              },
              {
                headerName: "Expected Expiry Date",
                field: "expiry_date",
                flex: 1.1,
                filter: "agDateColumnFilter",
                filterParams,
                valueFormatter,
              },
            ]}
            rowData={filteredData}
            pagination
            paginationPageSize={20}
          />
        </div>
      )}
    </section>
  );
};

export default Patent;
