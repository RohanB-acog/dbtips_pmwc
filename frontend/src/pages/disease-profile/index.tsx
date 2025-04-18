import { useState, useEffect } from 'react';
import Description from "./description";
import { useLocation } from 'react-router-dom';
import { parseQueryParams } from '../../utils/parseUrlParams';
import Ontology from "./ontology";

const DiseaseProfile = () => {
	const location = useLocation();

	const [indications, setIndications] = useState([]);
	useEffect(() => {
		const queryParams = new URLSearchParams(location.search);
		const {  indications } = parseQueryParams(queryParams);
		setIndications(indications);
	}, [location]);
		console.log(indications);
	return <div>
		<Description  indications={indications} />
		<Ontology indications={indications} />

	</div>;
};

export default DiseaseProfile;
