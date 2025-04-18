import { AgGridReact } from 'ag-grid-react';
import { fetchData } from '../../utils/fetchData';
import { useQuery } from 'react-query';
import { Empty } from 'antd';
import LoadingButton from '../../components/loading';

const Ontology = ({ hgnc_id, target, indications }) => {
	const payload = {
		target: target,
		diseases: indications,
	};

	const {
		data: targetOntologyData,
		error: targetOntologyError,
		isLoading: targetOntologyLoading,
	} = useQuery(
		['targetOntology', payload],
		() => fetchData(payload, '/target-profile/ontology/'),
		{
			enabled: !!target && !!indications.length,
		}
	);

	return (
		<section id='ontology' className='mt-12 px-[5vw]'>
			<h1 className='text-3xl font-semibold'>Ontology</h1>
			<p className='mt-2 italic font-medium'>
				Ontologies usually consist of a set of classes (or terms or concepts)
				with relations that operate between them. The Gene Ontology (GO)
				describes our knowledge of the biological domain with respect to three
				aspects: cellular component, biological process, and molecular function.
			</p>

			{targetOntologyLoading ? (
				<LoadingButton />
			) : targetOntologyError ? (
				<div className='ag-theme-quartz h-[80vh] max-h-[480px] mt-4 flex items-center justify-center'>
					<Empty description = "Error" />
				</div>
			) : (
				<div>
					<div className='ag-theme-quartz h-[80vh] max-h-[480px] mt-4'>
						<AgGridReact
							defaultColDef={{
								headerClass: 'font-semibold',
								flex: 1,
								sortable: true,
								filter: true,
								floatingFilter: true,
								autoHeight: true,
              wrapText: true,
              cellStyle: { whiteSpace: "normal", lineHeight: "20px" }
							}}
							columnDefs={[
								{ field: 'GO ID' },
								{
									field: 'Name',
									flex: 2,
									cellRenderer: (params) => (
										<a target='_blank' href={params.data.Link}>
											{params.value}
										</a>
									),
								},
								{ field: 'Aspect' },
								{ field: 'Evidence' },
								{ field: 'Gene Product',headerName: 'Gene product', },
								{ field: 'Source' },
							]}
							rowData={targetOntologyData?.ontology}
							pagination={true}
						/>
					</div>
					<div className='mt-8 overflow-x-scroll'>
						{/*  @ts-ignore */}
						<wc-go-ribbon subjects={hgnc_id}></wc-go-ribbon>
						<p slot='description' className=' text-[#7b7b7b] italic'>
							dark blue for higher volume and light blue for lower volume.
						</p>
					</div>
				</div>
			)}
		</section>
	);
};

export default Ontology;
