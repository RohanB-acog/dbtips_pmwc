import { useState, useEffect,useMemo } from 'react';
import { Checkbox, Select, Layout, Button } from 'antd';
import CytoscapeComponent from 'react-cytoscapejs';
import { JSONTree } from 'react-json-tree';
import { CloseOutlined } from '@ant-design/icons';
// import json from '../../assets/dgpg.graph.json';
import * as themes from 'redux-devtools-themes';

// import json from '../../assets/gggd.graph.json';



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

const commonProps = {
	animate: true,
	fit: true, // Fit the layout to the viewport
	padding: 30, // Padding between nodes and the viewport
	randomize: false, // Don't randomize positions
	nodeRepulsion: function () {
		return 4000; // Strong repulsion to prevent overlap
	},
	idealEdgeLength: function () {
		return 100; // Ideal edge length for good spacing
	},
};

const layoutOptions = [
	{
		...commonProps,
		name: 'cose',
		refresh: 10,
		componentSpacing: 100, // Space between disconnected components
		nodeOverlap: 10, // Prevent node overlap
		edgeElasticity: function () {
			return 5000; // Adjust elasticity for balance
		},
		gravity: 0.5, // Reduce gravity to spread nodes more evenly
		numIter: 1000, // Increase iterations for optimization
		initialTemp: 1000,
		coolingFactor: 0.99,
		minTemp: 1.0,
	},
	{
		...commonProps,
		name: 'breadthfirst',
		directed: true, // Treat the layout as directed
		circle: false, // Layout nodes in a hierarchy
		spacingFactor: 1.5, // Spacing between nodes
	},
	// {
	// 	...commonProps,
	// 	name: 'circle',
	// 	spacingFactor: 1.2, // Increase the distance between nodes in the circle
	// },
	{
		...commonProps,
		name: 'concentric',
		concentric: function (node) {
			return node.degree(); // Nodes with a higher degree are closer to the center
		},
		levelWidth: function (nodes) {
			return nodes.maxDegree() / 4; // Control width between levels
		},
	},
	{
		...commonProps,
		name: 'grid',
		rows: 4, // Number of rows
		cols: 4, // Number of columns
	},
];

const Graph = ({json,target}) => {
	const tree = useMemo(() => {
		const result = {
		  Disease: [],
		  Gene: [],
		  Pathway: [],
		  edge: []
		};
		
		json.elements.forEach(element => {
		  const type = element.data.type || 'edge';
		  if (!result[type]) result[type] = [];
		  result[type].push(element);
		});
		
		return result;
	  }, [json]);
	
	const [cy, setCy] = useState(null);
	// const [elements, setElements] = useState(json.elements);
	const [selected, setSelected] = useState(null);
	const [showNodes, setShowNodes] = useState(() => [
		...tree.Disease.map(node => node.data.id),
		...tree.Gene.map(node => node.data.id)
	  ]);
	const [highlightedNode, setHighlightedNode] = useState(null);
	const [showProperties, setShowProperties] = useState(false);
	const [openCheckboxGroup, setOpenCheckboxGroup] = useState({
		Pathway: true,
	});
	const [trackLayout, setTrackLayout] = useState(0);

	useEffect(() => {
		if (!cy) return;
		layout['name'] = layoutOptions[trackLayout].name;
		cy.layout(layoutOptions[trackLayout]).run();
	}, [trackLayout, cy]);

	const filterElementsByTypes = () => {
		const filteredNodes = json.elements.filter((el) =>
			showNodes.includes(el.data.id)
		);

		const filteredEdges = json.elements.filter(
			(edge) =>
				filteredNodes.some((node) => node.data.id === edge.data.source) &&
				filteredNodes.some((node) => node.data.id === edge.data.target)
		);

		// Clear existing elements if needed
		cy.elements().remove();
		cy.nodes().remove();
		cy.edges().remove();

		cy.add(filteredNodes.map((node) => ({ group: 'nodes', data: node.data })));
		cy.add(filteredEdges.map((edge) => ({ group: 'edges', data: edge.data })));
		cy.layout(layoutOptions[trackLayout]).run();

		// setElements([...filteredNodes, ...filteredEdges]);
	};

	// // Use effect to update elements whenever selectedTypes changes
	useEffect(() => {
		if (!cy) return;
		filterElementsByTypes();
		// Select the node with ID 'n1'
		// cy.getElementById('5445223').select();
	}, [cy, showNodes,json]); // eslint-disable-line

	const categories = useMemo(() => 
		Object.keys(tree).filter(key => key !== 'edge'),
		[tree]
	  );
	// Helper function to check if all nodes of a category are selected
	const isAllSelected = (category) =>
		tree[category].every((node) => showNodes.includes(node.data.id));

	// Helper function to check if some but not all nodes of a category are selected
	const isIndeterminate = (category) =>
		tree[category].some((node) => showNodes.includes(node.data.id)) &&
		!isAllSelected(category);

	 const options = useMemo(() => 
    json.elements
      .filter(node => categories.includes(node.data.type))
      .map(node => ({
        value: node.data.id,
        label: node.data.label
      })),
    [json.elements, categories]
  );

	return (
		<Layout style={{ width: '100%' }}>
			<Layout hasSider={true} style={{ position: 'relative' }}>
				<Layout.Content style={{ backgroundColor: 'white' }}>
					<section
						id='knowledge-graph-evidence'
						className='px-[5vw] py-20 bg-gray-50 mt-12'
					>
						<h1 className='text-3xl font-semibold'>Network Biology</h1>
						<p className='mt-2'>
							This knowledge graph section visualizes the connections between a
							single target and multiple disease pathways, illustrating how
							alterations in this target may impact various disease processes.
						</p>

						<h2 className='text-xl font-semibold subHeading mt-2'>
							Metapath description:
						</h2>
						<p className='mt-2'>
							Disease(s) → (genetically associated with) → Genes → (actively
							involved in) → Pathway → (actively involved in) → Target ({target})
							<br /> This metapath is used to reduce the inherently complex
							nature of the graph and enable the identification of pathways
							involving both disease(s) associated genes and the target of
							interest.
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
							<div
								className={`px-4 bg-slate-50 py-4 transition-all ${
									showProperties ? 'w-[20%]' : 'w-[20%]'
								}`}
							>
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
																.filter(
																	(node) => !showNodes.includes(node.data.id)
																) // Avoid duplicates
																.map((node) => node.data.id),
														];
														setShowNodes(newSelectedNodes);
													} else {
														// Remove all nodes of the category from showNodes
														const newSelectedNodes = showNodes.filter(
															(id) =>
																!tree[category].some(
																	(node) => node.data.id === id
																)
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
								elements={[]} // Pass elements to Cytoscape
								style={{
									width: showProperties ? '55%' : '80%',
									height: 720,
									border: '1px solid #111',
								}}
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
											'line-color': '#0505050f',
											'target-arrow-color': '#FF851B',
											'curve-style': 'bezier',
											// 'target-arrow-shape': 'triangle-backcurve',
											// 'arrow-scale': 1.5, // Adjust arrow size (optional)
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

							<Layout.Sider
								width='25%'
								className='min-w-[200px]'
								collapsible={true}
								collapsedWidth={0}
								collapsed={!showProperties}
								trigger={null}
								style={{ backgroundColor: '#fff' }}
							>
								{selected && (
									<div
										style={{ padding: '10px', position: 'relative' }}
										className='flex space-x-2'
									>
										{/* Close Button */}
										<Button
											type='text'
											icon={<CloseOutlined />}
											onClick={() => setShowProperties(false)}
											style={{
												position: 'absolute',
												top: 10,
												right: 10,
												border: 'none',
												background: 'transparent',
												fontSize: '16px',
											}}
										/>

										{/* Properties Content */}
										<div className='json-viewer' style={{ marginTop: '10px' }}>
											<h3 className='font-semibold'>{selected.label}</h3>
											<JSONTree
												theme={themes.apathy}
												data={selected.properties}
											/>
										</div>
									</div>
								)}
							</Layout.Sider>
						</div>
					</section>
				</Layout.Content>
			</Layout>
		</Layout>
	);
};

export default Graph;