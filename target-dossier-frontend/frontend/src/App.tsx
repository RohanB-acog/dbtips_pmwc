import { useState, useEffect, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Spin, Layout, FloatButton } from 'antd';
import TargetHeader from "./components/targetIndication"

import Header from './components/header';
import Footer from './components/footer';
import { parseQueryParams } from './utils/parseUrlParams';
import { ChatBot, useChatStore } from 'chatbot-component';
import ChatIcon from './assets/chat.svg?react';
import 'chatbot-component/dist/style.css';
import { config } from './utils/llmConfig';

import Home from './pages/home';
import TargetProfile from './pages/target-profile';
import Literature from './pages/evidence';
import Data from './pages/data';
// import Search from "./components/search"
import Models from './pages/models';
import MarketIntelligence from './pages/market-intelligence';
import TargetAssessment from './pages/target-assessment';
import DiseaseProfile from './pages/disease-profile';
// import ExportButton from './components/testExportButton';

// import { useQuery } from 'react-query';

const AppContent = () => {
	const [appState, setAppState] = useState({
		target: '',
		indications: [],
		data: [],
		loading: false,
		error: null,
	});

	const { isHidden, open, setConfig } = useChatStore();

	useEffect(() => {
		setConfig(config);
	}, []);

	useEffect(() => {
		const queryParams = new URLSearchParams(location.search);
		const { target, indications } = parseQueryParams(queryParams);

		setAppState((prevState) => ({
			...prevState,
			target: target,
			indications,
		}));
	}, [location]);

	return (
		<Layout style={{ width: '100%'  }}>
			<Header app_state={appState} />
			{/* <ExcelTemplate /> */}
			{/* <ExportButton /> */}
			{/* <div>{parse(htmlFile)}</div> */}
			{/* <Search  /> */}
			<TargetHeader target={appState.target} indications={appState.indications} />
			<Layout
				hasSider={true}
				style={{ position:"relative" }}
			>
				<Layout.Content style={{ backgroundColor: 'white', overflow: 'auto' }}>
					<main className=' min-h-[80vh]'>
						<Suspense
							fallback={
								<div className='flex items-center justify-center h-[80vh]'>
									<Spin tip='loading...' />
								</div>
							}
						>
							<Routes>
								<Route path='/' element={<Home setAppState={setAppState} />} />
								<Route path='/target-biology' element={<TargetProfile />} />
								{/* <Route path='/evidence' element={<Evidence />} /> */}
								<Route
									path='/market-intelligence'
									element={<MarketIntelligence />}
								/>
								<Route path='/disease-profile' element={<DiseaseProfile />} />
								<Route path='/literature' element={<Literature />} />
								<Route path='/data' element={<Data />} />
								<Route
									path='/target-assessment'
									element={<TargetAssessment />}
								/>
								<Route path='/model-studies' element={<Models />} />
							</Routes>
						</Suspense>
					</main>
				</Layout.Content>
				<Layout.Sider
					width='30%'
					className='min-w-[200px] bg-white overscroll-contain'
					collapsible={true}
					collapsedWidth={0}
					collapsed={isHidden}
					trigger={null}
					style={{
						// backgroundColor: '#fff',
						zIndex: '100',
						height: "80%",
						marginBottom: '32px',
						overflow: 'auto',
					}}
				>
					<div className='h-[89%] w-[30%] z-100 fixed pb-8  '>
						<ChatBot baseURL='/llm' />
					</div>
				</Layout.Sider>
			</Layout>
			{isHidden ? (
				<FloatButton
					icon={<ChatIcon width={18} height={18} />}
					onClick={open}
				/>
			) : null}
			<Footer />
		</Layout>
	);
};

const App = () => (
	<BrowserRouter>
		<AppContent />
	</BrowserRouter>
);

export default App;
