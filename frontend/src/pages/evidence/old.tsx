import { useState, useEffect } from 'react';
import { Drawer, Checkbox, Select, Button } from 'antd';
import CytoscapeComponent from 'react-cytoscapejs';
import { JSONTree } from 'react-json-tree';
import 'react-json-pretty/themes/monikai.css';
import json from '../../assets/dgpg.graph.json';

const tree = {
	Disease: [],
	Gene: [],
	Pathway: [],
};
json.elements.map((element) => {
	if (tree[element.data.type]) {
		tree[element.data.type].push(element);
	} else {
		const key = element.data.type || 'edge';
		tree[key] = [element];
	}
});

const layoutOptions = [
	{
		name: 'cose',
	},
	{
		name: 'breadthfirst',
		directed: true, // Treat the layout as directed
	},
	{
		name: 'circle',
	},
	{
		name: 'concentric',
	},
	{
		name: 'grid',
		rows: 4,
		cols: 4,
	},
];

const layout = {
	name: 'cose',
	animate: true,
	animationThreshold: 250,
	refresh: 10,
	fit: true,
	padding: 30,
	randomize: false,
	componentSpacing: 100, // Extra space between disconnected components
	nodeRepulsion: function () {
		return 4000; // Strong repulsion to prevent overlapping
	},
	nodeOverlap: 10, // Increase to ensure no overlap
	idealEdgeLength: function () {
		return 100; // Longer edge length for more spacing
	},
	edgeElasticity: function () {
		return 5000; // Adjust edge elasticity
	},
	gravity: 0.5, // Reduce gravity to prevent inward clustering
	numIter: 1000, // Increase iterations for better optimization
	initialTemp: 1000,
	coolingFactor: 0.99,
	minTemp: 1.0,
};

const Graph = () => {
	const [cy, setCy] = useState(null);
	const [elements, setElements] = useState(json.elements);
	const [selected, setSelected] = useState(null);
	const [showNodes, setShowNodes] = useState([
		...tree['Disease'].map((node) => node.data.id),
		...tree['Gene'].map((node) => node.data.id),
	]);
	const [highlightedNode, setHighlightedNode] = useState(null);
	const [showProperties, setShowProperties] = useState(false);
	const [openCheckboxGroup, setOpenCheckboxGroup] = useState({
		Pathway: true,
	});
	const [trackLayout, setTrackLayout] = useState(0);

	const filterElementsByTypes = () => {
		const filteredNodes = json.elements.filter((el) =>
			showNodes.includes(el.data.id)
		);

		const filteredEdges = json.elements.filter(
			(edge) =>
				filteredNodes.some((node) => node.data.id === edge.data.source) &&
				filteredNodes.some((node) => node.data.id === edge.data.target)
		);

		setElements([...filteredNodes, ...filteredEdges]);
	};

	useEffect(() => {
		if (!cy) return;
		layout['name'] = layoutOptions[trackLayout].name;
		cy.layout(layoutOptions[trackLayout]).run();
	}, [trackLayout, cy]);

	// // Use effect to update elements whenever selectedTypes changes
	useEffect(() => {
		if (!cy) return;
		filterElementsByTypes();
		// Select the node with ID 'n1'
		// cy.getElementById('5445223').select();
	}, [cy, showNodes]); // eslint-disable-line

	const categories = Object.keys(tree).filter((key) => key !== 'edge'); // Get all keys except "edge"

	// Helper function to check if all nodes of a category are selected
	const isAllSelected = (category) =>
		tree[category].every((node) => showNodes.includes(node.data.id));

	// Helper function to check if some but not all nodes of a category are selected
	const isIndeterminate = (category) =>
		tree[category].some((node) => showNodes.includes(node.data.id)) &&
		!isAllSelected(category);

	const options = [];

	elements.map((node) => {
		if (categories.includes(node.data.type)) {
			options.push({
				value: node.data.id,
				label: node.data.label,
			});
		}
	});

	// function getRandomLayoutOption() {
	// 	const randomIndex = Math.floor(Math.random() * layoutOptions.length);
	// 	return layoutOptions[randomIndex];
	// }

	// console.log('layout', layout);

	return (
		<section
			id='knowledge-graph-evidence'
			className='px-[5vw] py-20 bg-gray-50 mt-12'
		>
			<h1 className='text-3xl font-semibold'>Network Biology</h1>
			<p className='mt-2'>
				This knowledge graph section visualizes the connections between a single
				target and multiple disease pathways, illustrating how alterations in
				this target may impact various disease processes.
			</p>

			<h1 className='text-xl font-semibold mt-2'>Metapath description:</h1>
			<p className='mt-2'>
				Disease(s) → (genetically associated with) → Genes → (actively involved
				in) → Pathway → (actively involved in) → Target (TNFRSF4)
				<br /> This metapath is used to reduce the inherently complex nature of
				the graph and enable the identification of pathways involving both
				disease(s) associated genes and the target of interest.
			</p>

			<div className='flex justify-between items-center gap-x-2 ml-[22%] mt-4'>
				<div className='flex gap-x-2 items-center'>
					<label htmlFor=''>Search node</label>
					<Select
						showSearch
						optionFilterProp='label'
						defaultValue=''
						value={highlightedNode}
						style={{ width: 320 }}
						onChange={(value) => {
							cy.nodes().unselect();
							cy.getElementById(value).select();
							setHighlightedNode(value);
						}}
						options={options}
					/>
				</div>

				<div className='flex items-center gap-x-2'>
					{/* <label htmlFor=''></label> */}
					<Button
						onClick={() => {
							setTrackLayout((prev) => {
								if (prev == layoutOptions.length - 1) return 0;
								return prev + 1;
							});
						}}
					>
						Change Layout
						{/* <span className='material-symbols-outlined'>shuffle</span> */}
					</Button>
				</div>
			</div>

			<div className='mt-4 flex justify-center gap-x-8'>
				<div className='w-[20%] px-8 bg-slate-50 py-4'>
					{categories.map((category) => (
						<div key={category} className='my-4'>
							<div className='flex items-center gap-x-1'>
								{/* Select all checkbox for each category */}
								<Checkbox
									indeterminate={isIndeterminate(category)} // Check if some but not all nodes are selected
									onChange={(e) => {
										if (e.target.checked) {
											// Add all nodes of the category to showNodes
											const newSelectedNodes = [
												...showNodes,
												...tree[category]
													.filter((node) => !showNodes.includes(node.data.id)) // Avoid duplicates
													.map((node) => node.data.id),
											];
											setShowNodes(newSelectedNodes);
										} else {
											// Remove all nodes of the category from showNodes
											const newSelectedNodes = showNodes.filter(
												(id) =>
													!tree[category].some((node) => node.data.id === id)
											);
											setShowNodes(newSelectedNodes);
										}
									}}
									checked={isAllSelected(category)} // Check if all nodes of the category are selected
								>
									{category}s
								</Checkbox>

								<button
									onClick={() => {
										setOpenCheckboxGroup((prev) => ({
											...prev,
											[category]: !prev[category],
										}));
									}}
								>
									<span className='material-symbols-outlined text-3xl pt-2'>
										arrow_drop_down
									</span>
								</button>
							</div>

							{/* Dynamic Checkbox group for each category */}
							{openCheckboxGroup[category] ? (
								<Checkbox.Group
									style={{
										marginTop: '10px',
										marginLeft: 12,
										display: 'grid',
										gridTemplateColumns: '1fr',
										rowGap: 8,
										maxHeight: 450,
										maxWidth: 200,
										overflow: 'scroll',
									}}
									value={showNodes.filter((id) =>
										tree[category].some((node) => node.data.id === id)
									)} // Filter the selected nodes by category
									onChange={(newValues) => {
										// Get current category node IDs
										const categoryNodeIds = tree[category].map(
											(node) => node.data.id
										);

										// Remove deselected nodes of this category and add the new selections
										const updatedSelectedNodes = [
											...showNodes.filter(
												(id) => !categoryNodeIds.includes(id)
											), // Remove existing category nodes
											...newValues, // Add the newly selected nodes
										];

										setShowNodes(updatedSelectedNodes);
									}}
									options={tree[category]
										.map((node) => ({
											value: node.data.id,
											label: node.data.label,
										}))
										.sort((a, b) => a.label.localeCompare(b.label))}
								/>
							) : null}
						</div>
					))}
				</div>

				{/* Cytoscape Graph */}

				<CytoscapeComponent
					cy={(cy) => {
						setCy(cy); // Set Cytoscape instance on load

						cy.on('tap', 'node', (evt) => {
							const node = evt.target?.data();
							setShowProperties(true);
							setSelected(node);
							// setHighlightedNode(node.data.id);
						});

						cy.on('tap', 'edge', (evt) => {
							const data = evt.target?.data();
							setSelected(data);
							setShowProperties(true);
						});
					}}
					elements={elements} // Pass elements to Cytoscape
					style={{ width: '80%', height: 720, border: '1px solid #111' }}
					layout={layout}
					minZoom={0.5}
					maxZoom={2}
					stylesheet={[
						{
							selector: 'node',
							style: {
								label: 'data(label)',
								'text-valign': 'bottom',
								'text-halign': 'center',
								width: 10,
								height: 10,
								'font-size': '16px',
								color: '#111',
							},
						},
						{
							selector: 'edge',
							style: {
								width: 1,
								color: '#09090B',
								// label: 'data(label)',
								'text-halign': 'center',
								'text-valign': 'top',
								'font-size': '6px',
								'line-color': '#505050',
								'target-arrow-color': '#FF851B',
								// 'curve-style': 'bezier',
								'curve-style': 'straight',
								'text-wrap': 'wrap', // Enable text wrapping
								'text-max-width': '80', // Set a max width for the label
								'text-rotation': 'autorotate',
							},
						},
						{
							selector: 'node[type = "Disease"]',
							style: {
								'background-color': '#e11d48',
								width: 50,
								height: 50,
							},
						},
						{
							selector: 'node[type = "Gene"]',
							style: {
								'background-color': '#22c55e',
								width: 50,
								height: 50,
							},
						},
						{
							selector: 'node[type = "Pathway"]',
							style: {
								'background-color': '#3b82f6',
								width: 50,
								height: 50,
							},
						},
						{
							selector: 'node:selected',
							css: {
								'background-color': 'yellow',
								// shape: 'star',
								'border-width': 8,
								'border-style': 'double',
							},
						},
					]}
				/>

				{/* Node Type Selection */}
				<Drawer
					size='large'
					title={selected?.label ? selected.label : 'Properties'}
					onClose={() => {
						// setSelected(null);
						setShowProperties(false);
					}}
					open={showProperties}
				>
					{selected ? <JSONTree data={selected.properties}></JSONTree> : null}
				</Drawer>
			</div>
		</section>
	);
};

export default Graph;
