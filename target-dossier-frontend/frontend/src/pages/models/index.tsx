import { useLocation } from "react-router-dom";
import { parseQueryParams } from "../../utils/parseUrlParams";
import { useEffect, useState,  } from "react";
import ModelStudies from "./model-studies";
const Model = () => {
    const location = useLocation();
    const [indications, setIndications] = useState([]);
    useEffect(() => {
        const queryParams = new URLSearchParams(location.search);
        const {  indications } = parseQueryParams(queryParams);
        setIndications(indications);
      }, [location]);
  return (
      <ModelStudies indications={indications} />
    )
}

export default Model