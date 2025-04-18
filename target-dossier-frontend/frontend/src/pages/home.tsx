import { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button, Form, Select, ConfigProvider, Tag, Popover } from 'antd';
import type { FormProps } from 'antd';
import { capitalizeFirstLetter } from '../utils/helper';
import gifImage from '../assets/Cover_page_TD.png';
import { parseQueryParams } from '../utils/parseUrlParams';

// import { fetchData } from '../utils/fetchData';
import { Highlight } from "@orama/highlight";
import parse from "html-react-parser";


type FieldType = {
  target?: string;
  indications?: string[];
};

type GeneSuggestion = {
  id: string;
  approvedSymbol: string;
  matched_column: string;
};

type TIndication = {
  id: string;
  name: string;
  matched_column: string;
};



const IndicationsDefaultState: TIndication[] = [];

const highlighter = new Highlight();
const HighlightText = (text: string, searchTerm: string) => {
  return highlighter.highlight(text, searchTerm);
};

const fetchGeneData = async (input: string): Promise<{ data: GeneSuggestion[] }> => {
  const response = await fetch(`${import.meta.env.VITE_API_URI}/genes/lexical?query=${input}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  const text = await response.text();
  if (!response.ok) {
    try {
      const json = JSON.parse(text);
      throw new Error(json.message || 'An error occurred');
    } catch {
      throw new Error(text);
    }
  }

  return JSON.parse(text);
};

const Home = ({ setAppState }: { setAppState: (prev: any) => any }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const [form] = Form.useForm();
  // const [options, setOptions] = useState<IndicationSuggestion[]>([]);
  
  const [targetOptions, setTargetOptions] = useState<GeneSuggestion[]>([]);

  const [target, setTarget] = useState<string>('');
  const [indications, setIndications] = useState<TIndication[]>(IndicationsDefaultState);
  const [geneLoading, setGeneLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState("");
  const [geneInput, setGeneInput] = useState("");
  const [selectedIndications, setSelectedIndications] = useState<string[]>([]);

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const { target, indications } = parseQueryParams(queryParams);

    const parsedIndications = indications
      ? indications.map((indication: string) => capitalizeFirstLetter(indication))
      : [];

    setTarget(target || '');
    setSelectedIndications(parsedIndications);

    form.setFieldsValue({
      target,
      indications: parsedIndications,
    });
  }, [location, form]);

  // const fetchSuggestions = async (query: string) => {
  //   setLoading(true);
  //   try {
  //     const payload = { queryString: query };
  //     const response = await fetchData(payload, '/search');
  //     const suggestions = response.data.search.hits;
  //     setOptions(suggestions);
  //   } catch (error) {
  //     console.error('Error fetching suggestions:', error);
  //   }
  //   setLoading(false);
  // };

  useEffect(() => {
    const controller = new AbortController();

    if (!input.length) return;
    setLoading(true);
    const HOST = `${import.meta.env.VITE_API_URI}`;

    axios
      .get(`${HOST}/phenotypes/lexical?query=${input}`, {
        signal: controller.signal,
      })
      .then((response) => {
        setIndications(response.data.data ?? []);
      })
      .catch((error) => {
        if (axios.isCancel(error)) {
          console.log("Request canceled:", error.message);
        } else {
          console.error(
            "Error while fetching suggestions/indications: ",
            error.message
          );
        }
      })
      .finally(() => {
        setLoading(false);
      });

    return () => {
      controller.abort();
    };
  }, [input]);

  useEffect(() => {
    const controller = new AbortController();

    if (!geneInput.length) return;
    setGeneLoading(true);

    fetchGeneData(geneInput)
      .then((response) => {
        setTargetOptions(response.data ?? []);
      })
      .catch((error) => {
        console.error("Error while fetching gene suggestions: ", error.message);
      })
      .finally(() => {
        setGeneLoading(false);
      });

    return () => {
      controller.abort();
    };
  }, [geneInput]);

  const handleIndicationSelect = (value: string) => {
    setSelectedIndications((prev) => {
      const isSelected = prev.includes(value);
      const updated = isSelected
        ? prev.filter((item) => item !== value) // Remove if already selected
        : [...prev, value]; // Add if not selected

      form.setFieldsValue({ indications: updated }); // Sync with the Form & session storage
      sessionStorage.setItem("selectedIndications", JSON.stringify(updated));
      setInput(""); // Clear the search input after selection
      return updated;
    });
  };

  const handleTargetSelect = (value: string) => {
    setTarget(value);
    form.setFieldsValue({ target: value });
    setGeneInput("");
  };

  const onFinish: FormProps<FieldType>['onFinish'] = (values) => {
    const encodedIndications = values.indications
      ?.map((indication) => `"${capitalizeFirstLetter(indication)}"`)
      .join(',');

    setAppState((prev: any) => ({
      ...prev,
      target: values.target,
      indications: values.indications,
    }));

    navigate(`/target-biology?target=${values.target}&indications=${encodeURIComponent(encodedIndications || '')}`);
  };
const isButtonDisabled= target==="" 
  const dropdownRenderIndications = () => {
    if (loading) return <p className="px-4 py-2">Loading...</p>;
    if (!input.length) {
      return <p className="px-4 py-2">Start typing to search</p>;
    }
    if (!loading && !indications.length) {
      return <p className="px-4 py-2">No data</p>;
    }

    return (
      <ul className="max-h-80 overflow-y-auto text-sm">
        {indications.map((opt) => (
          <li
            key={opt.id}
            title={opt.name}
            onClick={() => handleIndicationSelect(opt.name)}
            className={`px-4 py-2 rounded ${
              selectedIndications.includes(opt.name)
                ? "bg-[#e6f4ff]"
                : "hover:bg-gray-100"
            }`}
          >
            <p>{opt.name}</p>

            <div className="mt-1">
              <Tag
                color="green"
                bordered={false}
                className="cursor-pointer text-xs"
              >
                {opt.id}
              </Tag>

              <Popover
                zIndex={1100}
                content={
                  <p className="max-w-80 text-sm max-h-52 overflow-y-scroll">
                    {parse(
                      HighlightText(opt.matched_column.split(":")[1], input)
                        .HTML
                    )}
                  </p>
                }
                placement="left"
              >
                <Tag className="cursor-pointer text-xs">
                  {opt.matched_column.split(":")[0]}
                </Tag>
              </Popover>
            </div>
          </li>
        ))}
      </ul>
    );
  };

  const dropdownRenderGene = () => {
    if (geneLoading) return <p className="px-4 py-2">Loading...</p>;
    if (!geneInput.length) {
      return <p className="px-4 py-2">Start typing to search</p>;
    }
    if (!geneLoading && !targetOptions.length) {
      return <p className="px-4 py-2">No data</p>;
    }

    return (
      <ul className="max-h-80 overflow-y-auto text-sm">
        {targetOptions.map((opt) => (
          <li
            key={opt.id}
            title={opt.approvedSymbol}
            onClick={() => handleTargetSelect(opt.approvedSymbol)}
            className={`px-4 py-2 rounded ${
              target === opt.approvedSymbol
                ? "bg-[#e6f4ff]"
                : "hover:bg-gray-100"
            }`}
          >
            <p>{opt.approvedSymbol}</p>

            <div className="mt-1">
              <Tag
                color="green"
                bordered={false}
                className="cursor-pointer text-xs"
              >
                {opt.id}
              </Tag>

              <Popover
                zIndex={1100}
                content={
                  <p className="max-w-80 text-sm max-h-52 overflow-y-scroll">
                    {parse(
                      HighlightText(opt.matched_column.split(":")[1], geneInput)
                        .HTML
                    )}
                  </p>
                }
                placement="left"
              >
                <Tag className="cursor-pointer text-xs">
                  {opt.matched_column.split(":")[1]}
                </Tag>
              </Popover>
            </div>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="bg-gradient-to-b h-[86vh] from-indigo-50 to-white hero">
      <div className="max-w-[96rem] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center mb-8">
          <h3 className="text-4xl text-gray-900 font-bold mb-4">
            Disease Biomarker & Target Insights Platform & Services (DBTIPS™)
          </h3>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Your guide to transforming complex data into actionable insights and empower target validation, and advancing precision-driven research and innovation.
          </p>
        </div>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-12">
          <div>
            <img
              src={gifImage}
              alt="Informative GIF"
              className="w-full h-[60vh] object-contain rounded-lg"
              loading="lazy"
            />
          </div>

          <div className="flex items-center w-full">
            <Form
              form={form}
              layout="vertical"
              labelWrap
              className="max-w-2xl mx-auto mb-16 w-full"
              onFinish={onFinish}
            >
              <ConfigProvider
                theme={{
                  components: {
                    Select: {
                      multipleItemHeightLG: 38,
                    },
                  },
                  token: {
                    controlHeight: 44,
                    paddingSM: 17,
                  },
                }}
              >
                <Form.Item name="target" label="Target:">
                  <Select
                    showSearch={true}
                    searchValue={geneInput}
                    placeholder="Please select a target"
                    onSearch={(value) => {
                      setGeneInput(value);
                      
                      if (!value) setTargetOptions([]);
                    }}
                    value={target}
                    onChange={handleTargetSelect}
                    dropdownRender={dropdownRenderGene}
                  />
                </Form.Item>
                <Form.Item name="indications" label="Indications:">
                  <Select
                    mode="multiple"
                    showSearch={true}
                    searchValue={input}
                    placeholder="Please select an indication"
                    onSearch={(value) => {
                      setInput(value);
                      if (!value) setIndications(IndicationsDefaultState);
                    }}
                    value={selectedIndications}
                    onChange={(value) => {
                      setSelectedIndications(value);
                      form.setFieldsValue({ indications: value });
                      setInput("");
                    }}
                    dropdownRender={dropdownRenderIndications}
                  />
                </Form.Item>
              </ConfigProvider>
              
              <Form.Item>
                <Button
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-6 px-6 rounded-xl font-semibold text-lg transition-all duration-200 flex items-center justify-center gap-2 hover:gap-3"
                  htmlType="submit"
                  disabled={isButtonDisabled}
                >
                  Search
                </Button>
              </Form.Item>
            </Form>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Home;