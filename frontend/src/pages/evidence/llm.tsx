import { useEffect, useState } from 'react';
import { Button, Spin, Modal } from 'antd';
import { useQuery } from 'react-query';
import rehypeRaw from 'rehype-raw';
import Markdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
const formatDisease = (array) => {
  if (!array?.length) return '';
  if (array.length === 1) return array[0];
  return `${array.slice(0, -1).join(', ')} and ${array[array.length - 1]}`;
};
const AskLLM = ({target,indications}) => {
	console.log(target,"target","indication",indications)
	const [question, setQuestion] = useState('');

    useEffect(() => {
        setQuestion(`Can you provide mechanistic insights into the role of ${target} in the pathogenesis of ${formatDisease(indications)}? Specifically, what pathways, biological processes, and cell types are implicated? Are there shared mechanisms across these diseases, and where do they converge or diverge in terms of immune response, tissue remodeling, or disease progression?`);
    }, [target]);
	const [shouldFetch, setShouldFetch] = useState(false);
	const [chunkId, setChunkId] = useState(null);
	const [chunk, setChunk] = useState('');
	const [showChunk, setShowChunk] = useState(false);

	const { data, error, status } = useQuery(
		'askQuestion',
		async () => {
			const response = await fetch(
				import.meta.env.VITE_API_URI + '/graphrag-answer/',
				{
					method: 'POST',
					headers: {
						'Content-Type': 'application/json', // Make sure the server expects JSON
					},
					body: JSON.stringify({
						question, // Ensure this is the correct structure expected by the server
					}),
				}
			);
			return response.json();
		},
		{
			enabled: shouldFetch,
			onError: () => {
				setShouldFetch(false);
			},
			onSuccess: () => {
				setShouldFetch(false);
			},
		}
	);

	useEffect(() => {
		const spanNodes = document.querySelectorAll('.reference');

		const handleClick = (e: Event) => {
			const target = e.target as HTMLElement;
			const dataRefValue = target.dataset.ref;
			setChunkId(dataRefValue);
		};

		spanNodes.forEach((node) => {
			node.addEventListener('click', handleClick);
		});

		return () => {
			spanNodes.forEach((node) => {
				node.removeEventListener('click', handleClick);
			});
		};
	}, [data]);

	useQuery(
		'getLinks',
		async () => {
			const res = await fetch(
				import.meta.env.VITE_API_URI + '/fetch-chunk/' + chunkId,
				{
					method: 'GET',
					headers: {
						'Content-Type': 'application/json', // Make sure the server expects JSON
					},
				}
			);

			return res.json();
		},
		{
			enabled: chunkId?.length > 0 ? true : false,
			onError: () => {
				setChunkId('');
			},
			onSuccess: (data) => {
				console.log('data', data);
				// window.open(data?.url, '_blank'); // Opens the link in a new tab
				setChunkId('');
				setChunk(data?.highlighted_paper);
				setShowChunk(true);
			},
		}
	);

	return (
		<section className='mt-12'>
			<h1 className='text-xl font-semibold'>LLM powered Literature Mining</h1>

			<div className='p-8 border mt-4'>
				<div className=''>
					<h2>
						<b>Question: </b>
					</h2>

					<textarea
						value={question}
						onChange={(e) => setQuestion(e.target.value)}
						style={{ width: '100%', minHeight: '100px', padding: '10px' }}
					/>

					<div className='flex justify-end'>
						<Button
							type='primary'
							onClick={() => {
								setShouldFetch(true);
							}}
						>
							Submit
						</Button>
					</div>
				</div>

				{status == 'loading' ? (
					<div className='h-[300px] flex items-center justify-center'>
						<Spin />
					</div>
				) : null}

				{!data && error ? <p>Unable to process the request</p> : null}

				{data && status != 'loading' ? (
					<div className='mt-1'>
						<h2>
							<b>Answer: </b>
						</h2>

						<div className='mt-4'>
							<Markdown
								className='markdown'
								rehypePlugins={[rehypeHighlight, rehypeRaw]}
							>
								{data?.answer}
							</Markdown>
						</div>
					</div>
				) : null}
			</div>

			<Modal
				open={showChunk}
				onCancel={() => {
					setShowChunk(false);
				}}
				footer={null}
				width={1440}
				style={{
					padding: 30,
					top: 20,
				}}
			>
				<div className='max-h-[80vh] overflow-y-scroll overflow-x-auto'>
					<Markdown
						className='markdown'
						rehypePlugins={[rehypeHighlight, rehypeRaw]}
					>
						{chunk}
					</Markdown>
				</div>
			</Modal>
		</section>
	);
};

export default AskLLM;
