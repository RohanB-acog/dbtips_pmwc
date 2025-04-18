import { useEffect } from 'react';
// import ProtvistaUniprot from 'protvista-uniprot';

// Define the custom element
// window.customElements.define('protvista-uniprot', ProtvistaUniprot);

const ProteinStructure = ({ uniprot_id }) => {
	useEffect(() => {
		// Any additional setup can go here
	}, []);

	return (
		<section id='protein-structure' className='mt-12 px-[5vw]  '>
			<h1 className='text-3xl font-semibold'>
				Protein structure, sequence, domain organization and mutation(s)
			</h1>
			<p className='mt-2 italic font-medium'>
				Protein structural information serves as the cornerstone for
				comprehending a target protein’s behavior, interactions, and therapeutic
				potential in drug development.
			</p>

			<div className='mt-4'>
				{/* @ts-expect-error */}
				<protvista-uniprot accession={uniprot_id} />
			</div>
		</section>
	);
};

export default ProteinStructure;
