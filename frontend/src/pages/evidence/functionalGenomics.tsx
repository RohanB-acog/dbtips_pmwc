import { AgGridReact } from "ag-grid-react";
import { useQuery } from "react-query";
import { fetchData } from "../../utils/fetchData";
import LoadingButton from "../../components/loading";
import { Empty } from "antd";

const Condition=(params)=>{
  if(params.value==="-") return "";
  return params.value
}
const Library=(params)=>{
  
  return <p>{params.value} | {params.data.LIBRARY_TYPE} | {params.data.METHODOLOGY}</p>
}
const CellularModel=(params)=>{
  return <p>{params.value} | {params.data.CELL_TYPE}</p>
}
const functionalGenomics = ({target}) => {
  const payload = {
    target: target,
  };
  const Publication=(params)=>{
    return <a target="_blank" href ={`https://pubmed.ncbi.nlm.nih.gov/${params.data.SOURCE_ID}`}>{params.value}</a>
  }

  const { data: genomicsData, error: genomicsError, isLoading: genomicsLoading } = useQuery(
    ["genomicDetails", payload],
    () => fetchData(payload, "/evidence/functional-genomics/"),
    { enabled: !!target  }
  );
console.log(genomicsData)
const activationCount = genomicsData
  ? genomicsData.results.filter(item => item.METHODOLOGY === "Activation").length
  : 0;

const knockoutCount = genomicsData
  ? genomicsData.results.filter(item => item.METHODOLOGY === "Knockout").length
  : 0;
  const organismCountMap = genomicsData?.results?.reduce((acc, item) => {
    const organism = item.ORGANISM_OFFICIAL;
    acc[organism] = (acc[organism] || 0) + 1;
    return acc;
  }, {});

  return (
<section id="genomics" className="px-[5vw] py-20 bg-gray-50 mt-12">
        <h1 className="text-3xl font-semibold">Functional Genomics</h1>
        <p className="italic font-medium mt-2">
        This section summarizes cellular phenotypes resulting from {target} perturbation across cell types, with publications and records on its significance and essentiality.
        </p>
    <p>
    </p>
      {genomicsLoading && <LoadingButton />}
      {genomicsError && (
        <div className="ag-theme-quartz mt-4 h-[80vh] max-h-[280px] flex items-center justify-center">
          <Empty />
        </div>
      )}
      {!genomicsLoading && !genomicsError && (
        <div className="mt-3">
          <span className="font-bold"> Summary: </span>
          <span className="text-sky-800">{genomicsData?.results?.length}</span> screens, <span className="text-sky-800">{knockoutCount}</span> knockout,  <span className="text-sky-800">{activationCount}</span> activation, 
         
           
            {organismCountMap &&
  Object.entries(organismCountMap).map(([organism, count], index, array) => (
    <span key={organism}>
      <span className="text-sky-800">{count as number}</span> in <span className="italic">{organism as string}</span>
      {index === array.length - 2 ? " and " : index < array.length - 2 ? ", " : ""}
    </span>
  ))
}

          

       
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
              { headerName: "Species", field: "ORGANISM_OFFICIAL", flex: 0.7 },
              { headerName: "Experiment", field: "EXPERIMENTAL_SETUP", width: 200 },
              { headerName: "Screen Rationale", field: "SCREEN_RATIONALE", width: 200 },
              { headerName: "Library", field: "LIBRARY",  flex:1.2, cellRenderer:Library },
              { headerName: "Cas Enzyme", field: "ENZYME", width: 200 },
              { headerName: "Cellular Model", field: "CELL_LINE", width: 200, cellRenderer:CellularModel },
              { headerName: "Experimental Conditions", field: "CONDITION_NAME", flex: 1.4, cellRenderer:Condition },
              { headerName: "Perturbation Phenotype", field: "PHENOTYPE", flex:1.6 },
              { headerName: "Publication", field: "SCREEN_NAME", width: 200, cellRenderer:Publication },
              
            ]}
            rowData={genomicsData? genomicsData.results:null}
            pagination
            paginationPageSize={20}
          />
        </div>
        </div>
      )}
    </section>  )
}

export default functionalGenomics