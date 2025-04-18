import { AgGridReact } from 'ag-grid-react';
import { fetchData } from '../../utils/fetchData';
import { useQuery } from 'react-query';
import { Empty } from 'antd';
import LoadingButton from '../../components/loading';
import { capitalizeFirstLetter } from '../../utils/helper';
const Paralogs = ({ target }) => {
	const payload = {
		target: target,
		
	};

	const { data: paralogsData, error: paralogsError,isLoading:paralogLoading } = useQuery(
		['paralogs', payload],
		() => fetchData(payload, '/target-assessment/paralogs/'),
		{
			enabled: !!target,
			refetchOnWindowFocus: false,
			staleTime: 5 * 60 * 1000,
			refetchOnMount: false,		}
	);

	// Fallback to empty array if data is null or undefined
	const rowData = [];

	if (paralogsData) {
		for (const key in paralogsData.paralogs) {
			const elements = paralogsData.paralogs[key];
			rowData.push(...elements);
		}
	}

	// console.log(rowData);

	// Check if rowData is empty before generating column definitions
	const defs =
		rowData.length > 0
			? Object.keys(rowData[0]).map((key) => {
					const def: any = { field: key ,headerName:capitalizeFirstLetter(key)}; // Type assertion to allow cellRenderer

					if (key === 'Paralog Pair URL') {
						def.cellRenderer = (params: any) =>
							params.value ? (
								<a target='_blank' href={params.value}>
									expression data
								</a>
							) : null;
					}

					if (key == 'Common GO slim') {
						def.minWidth = 540;
					}

					return def;
			  })
			: [];


	return (
		<section id='paralogs' className='mt-12 px-[5vw]'>
			<h1 className='text-3xl font-semibold'>Paralogs</h1>
			<p className='mt-2 s font-medium'>
			Homology for a target across selected species. Understanding paralogs can help avoid off-target effects and improve drug specificity.
			</p>

			{paralogLoading ? (
				<LoadingButton />
			) :
			
			paralogsError ? (
				// Error div with same height as AgGrid
				<div className='ag-theme-quartz mt-4 h-[80vh] max-h-[280px] flex items-center justify-center'>
					<Empty description={String(paralogsError)}/>
				</div>
			) : (
				rowData.length === 0 && paralogsData ? (
					<div className='ag-theme-quartz mt-4 h-[80vh] max-h-[280px] flex items-center justify-center'>
						<Empty description='No data available' />
					</div>
				) : 
				<div className='ag-theme-quartz mt-4 h-[80vh] max-h-[720px]'>
					<AgGridReact
						defaultColDef={{
							minWidth: 150,
							flex: 1,
							filter: true,
							sortable: true,
							floatingFilter: true,
							headerClass: 'font-semibold px-6 py-1',
							autoHeaderHeight: true,
							wrapHeaderText: true,
						}}
						columnDefs={defs}
						rowData={paralogsData ? rowData : null}
						pagination={true}
						enableRangeSelection={true}
						enableCellTextSelection={true}
					/>
				</div>
			)}
		</section>
	);
};

export default Paralogs;
