// import React from 'react'
import { Carousel, Card, Row, Col, ConfigProvider, Empty } from "antd";

const chunkImages = (images: any[], chunkSize: number) => {
    console.log("images", images);
    const result: any[][] = [];
    for (let i = 0; i < images.length; i += chunkSize) {
      result.push(images.slice(i, i + chunkSize));
    }
    return result;
  };
const carousel = ({networkBiologyData}) => {
  if(networkBiologyData && !networkBiologyData.results.length){
    return <Empty />
  }
    const imageChunks =
    networkBiologyData && Array.isArray(networkBiologyData.results)
      ? chunkImages(networkBiologyData.results, 3)
      : [];
  return (
<ConfigProvider
            theme={{
              components: {
                Carousel: {
                  arrowSize: 20,
                  arrowOffset: 5,
                },
              },
            }}
          >
            <Carousel arrows infinite={false}   >
              {imageChunks.map((chunk, index) => (
                <div key={index}>
                  <Row gutter={[16, 16]}>
                    {chunk.map((image: any, idx: number) => (
                      <Col key={idx} span={8}>
                        <a
                          href={image.pmcid? `https://pmc.ncbi.nlm.nih.gov/articles/${image.pmcid}`:`https://pubmed.ncbi.nlm.nih.gov/${image.pmid}`}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <Card
                            hoverable
                            className="custom-card"
                            cover={
                              <img alt={image.figtitle} src={image.image_url} />
                            }
                          >
                            <Card.Meta title={image.figtitle} />
                          </Card>
                        </a>
                      </Col>
                    ))}
                  </Row>
                </div>
              ))}
            </Carousel>
          </ConfigProvider>  )
}

export default carousel