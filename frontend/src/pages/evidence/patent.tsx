import {useState,useEffect} from 'react'
import { AgGridReact } from 'ag-grid-react';
import { useQuery } from 'react-query';
import { fetchData } from '../../utils/fetchData';
import LoadingButton from '../../components/loading';
import { Empty } from 'antd';

const PatentLink = (params) => {
    return (
      <a href={params.data.pdf} target="_blank" rel="noopener noreferrer">
        {params.value}
      </a>
    );
  };
const Patent = ({target,indications}) => {
const [rowData, setRowData] = useState([]);

console.log("indications", indications);
const payload = {
    target: target=="TNFRSF4"?"OX40":target,
    diseases: indications,
  };
  
  
const {data: patentData, error: patentError, isLoading: patentLoading} = useQuery(
["patentDetails",payload],
() => fetchData(payload, '/evidence/search-patent/'),
{
    enabled: !!target && !!indications.length,
  
  }
)
console.log("patent",patentData);
useEffect(() => {
    if (patentData) {
      const flattenedData = [];
      patentData.results.forEach(resultGroup => {
        resultGroup.results.forEach(patent => {
          flattenedData.push({
            ...patent,
            disease: resultGroup.disease // Add the disease to each row
          });
        });
      });
      setRowData(flattenedData);
    }
  
},[patentData])

console.log("flatten",rowData);
  // Framework components (for custom link rendering)
 

  return (
   <section id='patent' className='px-[5vw] py-20 bg-gray-50 mt-12'>
        <div className='flex items-center gap-x-2'>
            <h1 className='text-3xl font-semibold'>Patents</h1>
        </div>
    
        {/* <p className='mt-2 italic font-medium'>
            The following table contains patents that are associated with the target
            under consideration. Patents can provide valuable information about the
            target's potential therapeutic applications and the competitive landscape.
        </p> */}
      { patentLoading && <LoadingButton />      }
      {patentError && (
        <div className='ag-theme-quartz mt-4 h-[80vh] max-h-[280px] flex items-center justify-center'>
          <Empty description={`${patentError}`} />
        </div>
      )  
      }
      {!patentLoading && !patentError && (
        <div className='ag-theme-quartz mt-4 h-[80vh] max-h-[540px]'>
            <AgGridReact
            defaultColDef={{
                flex: 1,
                filter: true,
                sortable: true,
                floatingFilter: true,
                headerClass: 'font-semibold',
                autoHeight: true,
                wrapText: true,
                cellStyle: { whiteSpace: 'normal', lineHeight: '20px' },
            }}
            columnDefs={[
                {
                    headerName: "Disease",
                    field: "disease",
                    width: 200
                  },
                  {
                    headerName: "Patent No.",
                    field: "patent_id",
                    cellRenderer: PatentLink, // Custom renderer to show link
                    width: 200
                  },
                  { headerName: "Title", field: "title", flex:2 },
                  {
                    headerName: "Current Assignee",
                    field: "assignee",
                    valueFormatter: (params) => params.value ,
                    flex: 2,

                  },
                  {headerName: "Publication Date", field: "filing_date", width: 200, filter: 'agDateColumnFilter',
                  filterParams: {
                    comparator: (filterDate, cellValue) => {
                      const cellDate = new Date(cellValue);
                      cellDate.setHours(0, 0, 0, 0);
                      return cellDate.getTime() - filterDate.getTime();
                    },
                    dateFormat: 'mm/dd/yyyy'
                  },
                  valueFormatter: params => {
                    const date = new Date(params.value);
                    const day = String(date.getDate()).padStart(2, '0');
                    const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are zero-indexed
                    const year = date.getFullYear();
                    return `${month}/${day}/${year}`; // Display format for the row
                  }},
                  {headerName:"Grant Date", field:"grant_date", width:200, filter: 'agDateColumnFilter',filterParams: {
                    comparator: (filterDate, cellValue) => {
                      const cellDate = new Date(cellValue);
                      cellDate.setHours(0, 0, 0, 0);
                      return cellDate.getTime() - filterDate.getTime();
                    },
                    dateFormat: 'mm/dd/yyyy'
                  },
                  valueFormatter: params => {
                    if(!params.value)
                      return ""
                    const date = new Date(params.value);
                    const day = String(date.getDate()).padStart(2, '0');
                    const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are zero-indexed
                    const year = date.getFullYear();
                    return `${month}/${day}/${year}`; // Display format for the row
                  }},
                  {headerName:"Expiry Date", field:"expiry_date", width:200, filter: 'agDateColumnFilter',filterParams: {
                    comparator: (filterDate, cellValue) => {
                      const cellDate = new Date(cellValue);
                      cellDate.setHours(0, 0, 0, 0);
                      return cellDate.getTime() - filterDate.getTime();
                    },
                    dateFormat: 'mm/dd/yyyy'
                  },
                  valueFormatter: params => {
                    const date = new Date(params.value);
                    const day = String(date.getDate()).padStart(2, '0');
                    const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are zero-indexed
                    const year = date.getFullYear();
                    return `${month}/${day}/${year}`; // Display format for the row
                  }}
            ]}
            rowData={rowData}
            pagination={true}
            paginationPageSize={20}
            />
        </div>)}
    </section>
  )
}

export default Patent
