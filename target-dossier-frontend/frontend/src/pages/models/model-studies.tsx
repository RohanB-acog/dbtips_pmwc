import React, { useState,  useMemo } from "react";
import { Empty, Select, Tooltip } from "antd";
import parse from "html-react-parser";
import { fetchData } from "../../utils/fetchData";
import { useQuery } from "react-query";
import LoadingButton from "../../components/loading";
import Table from "../../components/testTable";
import ExportButton from "../../components/testExportButton";
import { capitalizeFirstLetter } from "../../utils/helper";

const { Option } = Select;

interface ModelStudiesProps {
	indications: string[];
}

interface MouseStudyRecord {
	Model: string;
	Gene: string;
	Species: string;
	Association: string;
	Disease: string;
	References: string[];
	SourceURL?: string;
}

function convertToArray(data: Record<string, any>): MouseStudyRecord[] {
	const result: MouseStudyRecord[] = [];
	Object.keys(data).forEach((disease) => {
		data[disease]['mouse_studies'].forEach((record: any) => {
			result.push({
				...record,
				Disease: capitalizeFirstLetter(disease),
			});
		});
	});
	return result;
}

const ModelStudies: React.FC<ModelStudiesProps> = ({ indications }) => {
	const [selectedIndication, setSelectedIndication] = useState<string>('All');

	const payload = {
		diseases: indications,
	};

	const apiEndpoint = '/evidence/mouse-studies/';

  const { 
    data, 
    isLoading, 
    isError, 
    isFetching 
  } = useQuery(
    ["mouseStudies", payload],
    () => fetchData(payload, apiEndpoint),
    {
      enabled: Boolean(indications?.length),
      
      // keepPreviousData: true, // Retain previous data while fetching
    }
  );

	// Memoized processed data to prevent unnecessary re-renders
	const processedData = useMemo(() => {
		if (data) {
			return convertToArray(data);
		}
		return [];
	}, [data]);


  // Filter data when processed data or selected indication changes
  const filteredData = useMemo(() => {
    if (processedData.length > 0) {
      return selectedIndication === "All"
        ? processedData
        : processedData.filter(
            (row) =>
              row.Disease.toLowerCase() === selectedIndication.toLowerCase()
          );
    }
    return [];
  }, [processedData, selectedIndication]);
  

	const handleSelect = (value: string) => {
		setSelectedIndication(value);
	};

	// Determine if we should show loading
	const showLoading = isLoading || isFetching;

	return (
		<section id='model-studies' className='mt-8 px-[5vw]'>
			<div className='flex items-center gap-x-2'>
				<h1 className='text-3xl font-semibold'>Animal models</h1>
			</div>

      <p className="mt-2  font-medium">
        This section provides model organisms with phenotypes relevant to the
        disease, supporting research on target identification, validation, and
        drug development.<br />
      
      </p>

			{showLoading ? (
				<div className='mt-4 h-[80vh] max-h-[280px] flex items-center justify-center'>
					<LoadingButton />
				</div>
			) : isError ? (
				<div className='flex items-center justify-center h-full'>
					<Empty description='Error fetching data' />
				</div>
			) : (
				// : filteredData.length === 0 ? (
				//   <div className="flex items-center justify-center h-full">
				//     <Empty description="No data available" />
				//   </div>
				// )
				<div>
					<div className='flex justify-between my-2'>
						<div>
							<span className='mt-4 mr-1'>Disease: </span>
							<Select
								style={{ width: 300 }}
								onChange={handleSelect}
								value={selectedIndication}
								disabled={showLoading}
							>
								<Option value='All'>All</Option>
								{indications.map((indication) => (
									<Option key={indication} value={indication}>
										{indication}
									</Option>
								))}
							</Select>
						</div>
						<ExportButton
							indications={indications}
							fileName='Animal-Models'
							endpoint='/evidence/mouse-studies/'
						/>
					</div>
					<div className='text-base'>
						<span className='font-bold'>Summary: </span>
						There are{' '}
						<span className='text-sky-800'>{processedData.length}</span> animal
						models available.
					</div>
					<div className='ag-theme-quartz mt-4'>
						<Table
							maxRows={processedData.length > 10 ? 10 : processedData.length}
							rowHeight={40}
							columnDefs={[
								{
									field: 'Model',
									flex: 3,
									headerName: 'Model',
									valueGetter: (params) => params.data.Model,
									cellRenderer: (params) => (
										<Tooltip title='Click to view phenotypes'>
											<a
												href={params.data.SourceURL}
												target='_blank'
												rel='noopener noreferrer'
											>
												{parse(params.value)}
											</a>
										</Tooltip>
									),
								},
								{
									field: 'Gene',
									flex: 3,
									headerName: 'Gene perturbed',
									valueGetter: (params) => {
										return params.data.Gene;
									},
								},

								{
									field: 'Species',
									headerName: 'Species',
									valueGetter: (params) => {
										return params.data.Species;
									},
									flex: 1,
									cellRenderer: (params) => {
										return <i>{params.value}</i>;
									},
								},
								// {
								//   field: "ExperimentalCondition",
								//   flex: 1.5,
								//   headerName: "Experimental Condition",

								//   valueGetter: (params) => {
								//    return params.data.ExperimentalCondition
								//   },
								//   cellRenderer: (params) => {
								//     if (params.value.length > 0) {
								//       return (
								//         <div>
								//           {params.value.map((item, index) => {
								//             const { name } = item.conditionRelationType;
								//             const conditionSummary = item.conditions[0]?.conditionSummary || 'N/A';
								//             return (

								//               <dl key={index}>
								//                 <dt>{name.replace(/_/, ' ')}: </dt> <dd>{conditionSummary}</dd>
								//               </dl>
								//             );
								//           })}
								//         </div>
								//       );
								//     } else {
								//       return null;
								//     }
								//   }

								// },

								{
									field: 'Association',
									flex: 1,
									headerName: 'Association',
									valueGetter: (params) => {
										return params.data.Association;
									},
									cellRenderer: (params) => {
										const type = params.value.toLowerCase();
										if (params.value == 'is_not_model_of')
											return <>does Not model</>;

										if (type === 'is_not_model_of') {
											return <>does not model</>;
										}

										const words = type
											?.replaceAll('_', ' ')
											.split(/(?:^| )not(?: |$)/, 2);
										return (
											<>
												{words?.[0]}
												{words?.length > 1 && <> not {words[1]}</>}
											</>
										);
									},
								},
								{
									field: 'Disease',
									headerName: 'Disease',
									valueGetter: (params) => {
										return params.data.Disease;
									},
								},

								// {
								//   field: "Evidence",
								//   flex: 1,
								//   headerName: "Evidence",

								//   valueFormatter: (params) => {
								//     if (params.value) {
								//       return params.value.join(", ");
								//     }
								//     return "";
								//   },

								// },

								{
									field: 'References',
									flex: 1.3,
									headerName: 'Reference (PMID)',
									cellRenderer: (params) =>
										params.value.map((value, index) => (
											<a
												key={index}
												className='mr-2'
												href={`https://pubmed.ncbi.nlm.nih.gov/${value}`}
												target='_blank'
											>
												{value}
												{params.value.length - 1 !== index ? ',' : ''}
											</a>
										)),
								},
								// ... rest of the column definitions remain the same
							]}
							rowData={filteredData}
						/>
					</div>
					<i className='text-base'>Source: Alliance of Genome Resources</i>
				</div>
			)}
		</section>
	);
};

export default ModelStudies;
