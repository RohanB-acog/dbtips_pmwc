import axios from "axios";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Form, Select, ConfigProvider, Tag, Popover,notification,Modal } from "antd";
import { Highlight } from "@orama/highlight";
import parse from "html-react-parser";
import type { FormProps } from "antd";
import gifImage from "../assets/hero_2.png";
import { fetchData } from "../utils/fetchData";
import { useQuery } from "react-query";

const highlighter = new Highlight();
const HighlightText = (text: string, searchTrem: string) => {
  return highlighter.highlight(text, searchTrem);
};

const IndicationsDefaultState: TIndication[] = [];
const Home = ({ setAppState }) => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalDescription, setModalDescription] = useState("");
  const [confirm, setConfirm] = useState(false)
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [payload, setPayload] = useState<{ diseases: string[] } | null>(null);
  const [indications, setIndications] = useState<TIndication[]>(
    IndicationsDefaultState
  );
  const [selectedIndications, setSelectedIndications] = useState<string[]>([]);

  // Load saved indications from session storage on component mount
  useEffect(() => {
    const savedIndications = sessionStorage.getItem("selectedIndications");
    if (savedIndications) {
      const parsedIndications = JSON.parse(savedIndications);
      form.setFieldsValue({ indications: parsedIndications });
      setSelectedIndications(parsedIndications);
    }
  }, [form]);

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

  // Handle form value changes and persist to session storage
  const onValuesChange = (_, allValues) => {
    setSelectedIndications(allValues.indications);

    // Save current selections to session storage
    sessionStorage.setItem(
      "selectedIndications",
      JSON.stringify(allValues.indications ?? [])
    );
  };
  const {
		data,
		
		isLoading,
		
	} = useQuery(
		['diseaseStatus', payload],
		() => fetchData(payload, '/dossier/disease-dossier-status/'),
		{
			enabled: !!payload,
			
		}
	);  // Handle form submission
  const onFinish: FormProps<FieldType>["onFinish"] = (values) => {
    // const encodedIndications = values.indications
    //   .map((indication) => `"${indication}"`)
    //   .join(",");
    setPayload({diseases:values.indications})
    // Save to app state
    // setAppState((prev) => ({
    //   ...prev,
    //   indications: values.indications,
    // }));

    // Navigate to disease profile
    // navigate(
    //   `/disease-profile?indications=${encodeURIComponent(encodedIndications)}`
    // );
  };
  useEffect(() => {
    if (data) {
      const cachedDiseases = data["cached diseases"] || [];
      const buildingDiseases = data["building diseases"] || [];
      if(data["cached diseases"]?.length >0){
        const encodedIndications = cachedDiseases
        .map((indication) => `"${indication}"`)
        .join(",");
          setAppState((prev) => ({
            ...prev,
            indications: data["cached diseases"],
          }));
        if (data["cached diseases"]?.length === payload?.diseases.length) {     
       navigate(`/disease-profile?indications=${encodeURIComponent(encodedIndications)}`);
     }
     else{
      setIsModalOpen(true);
      setModalDescription(`Dossier is available for ${cachedDiseases.join(", ")}. 
      It will take some time to build the dossier for ${buildingDiseases.join(", ")}.
      Do you want to continue?`)
      if(confirm){
        navigate(`/disease-profile?indications=${encodeURIComponent(encodedIndications)}`);

      }

     }
      }
     
   
      else {
        notification.warning({
          message: "Processing",
          description: "The dossier is being built. Please try again later.",
        });
      }
    }
  }, [data, navigate, payload,confirm]);

  const handleItemSelect = (value: string) => {
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

  const dropdownRender = () => {
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
            onClick={() => handleItemSelect(opt.name)}
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

  return (
    <div
      className="bg-gradient-to-b from-indigo-50 to-white hero h-[87vh]"
      id="home"
    >
      <div className="max-w-[96rem] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center mb-12">
          <h3 className="text-4xl text-gray-900 font-bold mb-4">
            Disease Biomarker & Target Insights Platform & Services (DBTIPS™)
          </h3>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Unlocking disease complexities to transform data into insights for
            disease characterization and precise therapeutic target
            identification.
          </p>
        </div>
        <section className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center mt-16">
          <div>
            <img
              src={gifImage}
              alt="Informative GIF"
              className="w-full h-[50vh] object-contain rounded-lg"
              loading="lazy"
            />
          </div>

          <div>
            <Form
              form={form}
              layout="vertical"
              labelWrap={true}
              style={{ width: "100%" }}
              onFinish={onFinish}
              onValuesChange={onValuesChange}
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
                    paddingSM: 12,
                  },
                }}
              >
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
                    
                    dropdownRender={dropdownRender}
                  />
                </Form.Item>
              </ConfigProvider>

              <Form.Item>
                <Button
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-6 px-6 rounded-xl font-semibold text-lg transition-all duration-200 flex items-center justify-center gap-2 hover:gap-3"
                  htmlType="submit"
                  disabled={selectedIndications.length > 0 ? false : true}
                  loading={isLoading}
                >
                  Search
                </Button>
              </Form.Item>
            </Form>
          </div>
          <Modal
           centered={true}
            open={isModalOpen}
            onOk={() => {setConfirm(true);setIsModalOpen(false)}}
            onCancel={() => {setIsModalOpen(false)}}
          >
            <p className="mr-2">

            {modalDescription}
            </p>

          </Modal>
        </section>
      </div>
    </div>
  );
};

export default Home;

type TIndication = {
  id: string;
  name: string;
  matched_column: string;
};

type FieldType = {
  indications?: string[];
};
