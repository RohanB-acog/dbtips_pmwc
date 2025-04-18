import { useState, useEffect,   } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { Dropdown } from 'antd';
import { parseQueryParams } from '../utils/parseUrlParams';

import AganithaLogo from '../assets/aganitha-logo.png';
import NotificationBell from "./notification"
const items = [
	
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
			},{
				key:"biomarkers", label:"Biomarkers", disabled:true
			}
		]
	},
	
	{
		key: 'market-intelligence',
		label: 'Market Intelligence',
		children: [
		  {key:"approvedDrug", label:"Approved drugs"},
		  { key: 'pipeline-by-indications', label: 'Indication pipeline' },
		  {
			key: 'opinionLeaders',
			label: 'Opinion leaders',
			children: [
			  { key: 'siteInvetigators', label: 'Site investigators', },
			  
			  { key: 'kol', label: 'Key influential leaders' },
			//   { key: 'kol', label: 'Key researchers' },
			  
			]
		  },
		  {
			key: 'patientStories',label:"Patient stories"
		  }
		]
	  },
	{
		key:"data", label:"Data",
		children:[
			{
				key:"rnaSeq", label:"RNA-seq datasets"
			},
			{
				key:"GenomicsStudies", label:"Genomics studies",
				children:[
					{
						key:"gwas-studies", label:"GWAS summary plot",
					},
					{
						key:"pgsCatalog", label:"Polygenic risk scores",
					},
				]

			}
			
		]
	},
	{
		key:"literature",	label:"Literature ",
		children:[
			{
				key:"literature-evidence", label:"Literature reviews"
			},
			{
				key:"knowledge-graph-evidence", label:"Disease pathways"
			},
			
		]
	},
	
	{
		key:"model-studies", label:"Models",
		children:[
			{
				key:"model-studies", label:"Animal models "
			}
		]
	},
	
	
];

const Header = ({ app_state }) => {
	const location = useLocation();
	const navigate = useNavigate();
	const [indications, setIndications] = useState([]);
	const [showNavMenu, setShowNavMenu] = useState(true);
	const [selectedKey, setSelectedKey] = useState(null);
	useEffect(() => {
		const queryParams = new URLSearchParams(location.search);
		const { indications } = parseQueryParams(queryParams);
		// setTarget(target);
		setIndications(indications);
	}, [location.search]);
	// Toggle nav visibility based on current route
	useEffect(() => {
		if (location.pathname === '/' || location.pathname === '/home'  || (location.pathname === '/notification' && indications.length === 0)) {
			setShowNavMenu(false);
		} else {
			setShowNavMenu(true);
		}
	}, [location]);

	// Scroll into view function
	const scrollIntoView = (id) => {
		const section = document.getElementById(id);
		const headerOffset = 80; // Height of the sticky header
		const elementPosition = section.getBoundingClientRect().top;
		const offsetPosition = elementPosition + window.scrollY - headerOffset;

		window.scrollTo({
			top: offsetPosition,
			behavior: 'smooth',
		});
	};

	// Helper to navigate and preserve query params (target and indications)
	const navigateWithParams = (path, key) => {

		// Join indications with double quotes and commas
		const indications = app_state.indications
			.map((indication) => `"${indication}"`)
			.join(',');

		// Navigate with target and formatted indications as query params
		navigate(`${path}?indications=${indications}`);

		// Scroll into view after navigation
		setTimeout(() => {
			scrollIntoView(key);
		}, 250);
	};

	// Build URL with encoded indications
	const buildUrlWithIndications = (baseUrl, indications) => {
		const searchParams = new URLSearchParams();
		// searchParams.set('target', target);

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
				<Link to='/' className='flex items-center gap-x-2  hover:text-black'>
					<img width={90} src={AganithaLogo} alt='Aganitha' />
					<div className='w-[1px] h-4 bg-[#555]' />
					<h2 className='text-base'>DBTIPS<sup>TM</sup> {"  "} - Disease Dossier</h2>
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
						 <NavLink
		to={buildUrlWithIndications(
			`/notification`,
			app_state.indications
		)}
		
	><NotificationBell data={app_state.indications} /></NavLink>
					</nav>
				) :
				<div className='mr-3'><NavLink
				to="/notification"
				
			><NotificationBell data={app_state.indications} /></NavLink></div> }
			</div>
		</header>
	);
};

export default Header;
