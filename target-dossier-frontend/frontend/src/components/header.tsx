import { useState, useEffect,   } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { Dropdown } from 'antd';
import AganithaLogo from '../assets/aganitha-logo.png';

const items = [
	// {
	// 	key:"home",label:"Home" ,
	// 	children:[
	// 		{
	// 			key:"home", label:"Home"
	// 		},
			
	// 	]
	// },
	{
		key: 'target-biology',
		label: 'Target Overview',
		children: [
			
			{
				key: 'target-description',
				label: 'Target description',
			},
			{
				key: 'taxonomy',
				label: 'Taxonomy',
			},
			{
				key: 'ontology',
				label: 'Ontology',
			},
			{
				key: 'protein-expression',
				label: 'RNA/Protein expressions',
			},
			{
				key: 'protein-structure',
				label: 'Protein structure',
			},
			{
				key: 'sub-cellular-location',
				label: 'Subcellular localization',
			},
		],
	},
	
	{
		key: 'disease-profile',
		label: 'Disease Overview',
		disabled: false,
		children:[
			{
				key:`disease-description`, label:`Description`,
			},
			{
				key:`disease-ontology`, label:`Ontology`
			},
			// {
			// 	key:"biomarkers", label:"Biomarkers", disabled:true
			// }
		]
	},

	
	
	{

		key: 'literature',
		label: 'Evidence',
		children: [
			{ key: 'literature-evidence', label: 'Literature' },
			// { key: 'knowledge-graph-evidence', label: 'Disease Pathophysiology' },
			// {
			// 	key: '',
			// 	label: 'Genomic Evidence',
			// 	disabled: true,
			// },
			{
				key: 'model-studies',
				label: 'Target perturbation phenotypes',
			},
			// {
			// 	key: 'genomics',
			// 	label: 'Functional Genomics',
			// },
			// {
			// 	key: 'rnaSeq',
			// 	label: 'RNA-seq Datasets',

			// },
			// {
			// 	key: '',
			// 	label: 'Real World Evidence',
			// 	disabled: true,
			// },
		],
	},
	{
		key: 'market-intelligence',
		label: 'Market Intelligence',
		children: [
		  {key:"approvedDrug", label:"Approved drugs"},
		  { key: 'pipeline-by-target', label: 'Target pipeline' },
		  { key: 'patent', label: 'Patents' },

		//   { key: 'pipeline-by-indications', label: 'Indication pipeline' },
		//   {
		// 	key: 'kol',
		// 	label: 'Opinion leaders',
		// 	children: [
		// 	  { key: 'kol', label: 'Site investigators', disabled:true },
		// 	  { key: 'kol', label: 'Key influential leaders' },
		// 	//   { key: 'kol', label: 'Key researchers' },
			  
		// 	]
		//   }
		]
	  },
	  

	{
		key: 'target-assessment',
		label: 'Target Assessment',
		children: [
			{
				key: 'targetability',
				label: 'Targetability',
			},
			{
				key: 'tractability',
				label: 'Tractability',
			},
			{
				key: 'paralogs',
				label: 'Paralogs',
			},
			{
				key:"geneEssentialityMap",
				label:"Gene essentiality map"
			}
		],
	},
];

const Header = ({ app_state }) => {
	const location = useLocation();
	const navigate = useNavigate();
	const [showNavMenu, setShowNavMenu] = useState(true);
	const [selectedKey, setSelectedKey] = useState(null);

	// Toggle nav visibility based on current route
	useEffect(() => {
		if (location.pathname === '/' || location.pathname === '/home') {
			setShowNavMenu(false);
		} else {
			setShowNavMenu(true);
		}
	}, [location]);

	// Scroll into view function
	const scrollIntoView = (id) => {
		const section = document.getElementById(id);
		const headerOffset = location.pathname=="/"?60:130; // Height of the sticky header
		const elementPosition = section.getBoundingClientRect().top;
		const offsetPosition = elementPosition + window.scrollY - headerOffset;

		window.scrollTo({
			top: offsetPosition,
			behavior: 'smooth',
		});
	};

	// Helper to navigate and preserve query params (target and indications)
	const navigateWithParams = (path, key) => {
		const target = app_state.target || '';
		// Join indications with double quotes and commas
		const indications = app_state.indications
			.map((indication) => `"${indication}"`)
			.join(',');
		

		// Navigate with target and formatted indications as query params
		navigate(`${path}?target=${target}&indications=${indications}`);

		// Scroll into view after navigation
		setTimeout(() => {
			scrollIntoView(key);
		}, 250);
	};

	// Build URL with encoded indications
	const buildUrlWithIndications = (baseUrl, target, indications) => {
		const searchParams = new URLSearchParams();
		searchParams.set('target', target);

		// Format indications with double quotes and comma-separated
		const encodedIndications = indications
			.map((indication) => `"${indication}"`)
			.join(',');
		searchParams.set('indications', encodedIndications);

		return `${baseUrl}?${searchParams.toString()}`;
	};
	const handlePressEffect = (e) => {
		e.target.classList.add('pressed');
		setTimeout(() => e.target.classList.remove('pressed'), 300); // Duration matches the CSS animation
	  };

	return (
		<header className='border-b sticky top-0 z-10 bg-white pl-[5vw] py-4'>
			<div className='flex items-center justify-between'>
				<Link to={buildUrlWithIndications("/",app_state.target,
												app_state.indications)} className='flex items-center gap-x-2 hover:text-black '>
					<img width={90} src={AganithaLogo} alt='Aganitha' />
					<div className='w-[1px] h-4 bg-[#555]' />
					<h2 className='text-base'>DBTIPS<sup>TM</sup> {"  "} - Target Dossier</h2>
				</Link>

				{showNavMenu ? (
					<nav className='flex items-center px-2 mr-5 gap-1  ' >
						{items.map((page, index) => (
							<div key={index}>
								<Dropdown
									menu={{
										items: page?.children || [],
										onClick: (e) => {
											setSelectedKey(e.key);

											// Navigate to the selected page with query params
											if (page.key !== location.key) {
												navigateWithParams(`/${page.key}`, e.key);
											} else {
												scrollIntoView(e.key);
											}
										},
										selectable: true,
										selectedKeys: [selectedKey],
									}}
								>
									{page.disabled ? (
										<span className='text-base cursor-not-allowed text-zinc-400'>
											{page.label}
										</span>
									) : (
										<NavLink
											to={buildUrlWithIndications(
												`/${page.key}`,
												app_state.target,
												app_state.indications
											)}
											// style={({ isActive }) => ({
											// 	color: isActive ? '#1677ff' : 'black',
											// })}
											className={"nav-link"}
											onMouseDown={handlePressEffect} // Add the pressed class on click

											// className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
										>
											<span className='flex items-center'>
												<span className='text-base  px-2  border-gray-200 '>{page.label}
												{page.children ? (
													<span className='material-symbols-outlined text-2xl align-middle	'>
														arrow_drop_down
													</span>
												) : null}
												</span>
												
											</span>
										</NavLink>
									)}
								</Dropdown>
							</div>
						))}
					</nav>
				) : null}
			</div>
		</header>
	);
};

export default Header;
