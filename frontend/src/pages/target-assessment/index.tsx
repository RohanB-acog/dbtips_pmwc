import { useState, useEffect } from 'react';
import Targetability from './targetability';
import Tractability from './tractability';
import Paralogs from './paralogs';
import { useLocation } from 'react-router-dom';
import { parseQueryParams } from '../../utils/parseUrlParams';

const TargetAssessment = () => {
	const location = useLocation();
	const [target, setTarget] = useState('');

	useEffect(() => {
		const queryParams = new URLSearchParams(location.search);
		const { target } = parseQueryParams(queryParams);
		setTarget(target);
	}, [location]);
	return (
		<section>
			<Targetability target={target} />
			<Tractability target={target}  />
			<Paralogs target={target}  />
		</section>
	);
};

export default TargetAssessment;
