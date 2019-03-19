
import getConfig from 'next/config';
const {publicRuntimeConfig} = getConfig();
const {PUBLIC_IP} = publicRuntimeConfig;
const {ELASTIC_PORT} = publicRuntimeConfig;
const {ELASTIC_IP} = publicRuntimeConfig;
const {ELASTIC_INDEX} = publicRuntimeConfig;
const {AUTH_TOKEN} = publicRuntimeConfig;

console.log('PUBLIC_IP: ' + PUBLIC_IP);
console.log('ELASTIC_PORT: ' + ELASTIC_PORT);
console.log('ELASTIC_IP: ' + ELASTIC_IP);
console.log('ELASTIC_INDEX: ' + ELASTIC_INDEX);
console.log('AUTH_TOKEN: ' + AUTH_TOKEN);
if (AUTH_TOKEN === undefined) {
  throw new Error('AUTH_TOKEN is undefined');
}


var resultComponent = {
  componentId: "results",
  dataField: "original_title.search",
  react: {
    and: [
      "mainSearch",
      "modality-list",
      "gender-list",
      "bodypart-list",
      "age-slider",
      "acquisitiondate-range",
      "tagCloud"
    ]
  },
  pagination: true,
  className: "Result_card",
  paginationAt: "bottom",
  pages: 5,
  size: 10,
  Loader: "Loading...",
  noResults: "No results found...",
  // sortOptions: [
  //   {
  //     dataField: "revenue",
  //     sortBy: "desc",
  //     label: "Sort by Revenue(High to Low) \u00A0"
  //   },
  //   {
  //     dataField: "popularity",
  //     sortBy: "desc",
  //     label: "Sort by Popularity(High to Low)\u00A0 \u00A0"
  //   },
  //   {
  //     dataField: "vote_average",
  //     sortBy: "desc",
  //     label: "Sort by Ratings(High to Low) \u00A0"
  //   },
  //   {
  //     dataField: "original_title.raw",
  //     sortBy: "asc",
  //     label: "Sort by Title(A-Z) \u00A0"
  //   }
  // ],
  onData: res => ({
    description: (
      <div className="main-description">
        <div className="ih-item square effect6 top_to_bottom">

          <a
            target="#"
            href={
              "http://" + PUBLIC_IP + 
              ":8080/index.html?input=http://" + res.dicom_filepath
            }
          >
            <div className="img">
              <img
                src={res.thumbnail_filepath}
                alt={res.original_title}
                className="result-image"
              />
            </div>
            <div className="info colored">
              <h3 className="overlay-title">
                {res.original_title}
                <button
                  type="button"
                  className="btn btn-dark"
                  style={{ marginLeft: "100px" }}
                  onClick={e => AddToCollection(e, res)}
                >
                  <i className="fa fa-plus" />{" "}
                </button>
              </h3>

              <div className="overlay-description">{res.tagline}</div>

              <div className="overlay-info">
                <div className="rating-time-score-container">
                  <div className="sub-title Modality-data">
                    <b>
                      Modality
                      <span className="details"> {res.Modality} </span>
                    </b>
                  </div>
                  {/*                    <div className="time-data">
                    <b>
                      <span className="time">
                        <i className="fa fa-clock-o" />{" "}
                      </span>{" "}
                      <span className="details">{res.time_str}</span>
                    </b>
                  </div>*/}

                  {Number.isInteger(res.PatientAgeInt) && (
                    <div className="sub-title Age-data">
                      <b>
                        Age:
                        <span className="details"> {res.PatientAgeInt}</span>
                      </b>
                    </div>
                  )}
                </div>

                <div className="revenue-lang-container">
                  {res.AcquisitionDate && (
                    <div className="sub-title AcquisitionDate-data">
                      <b>
                        Acquisition Date:
                        <span className="details">
                          {" "}
                          {res.AcquisitionDatePretty}
                        </span>
                      </b>
                    </div>
                  )}

                  {/*<div className="revenue-data">
                    <b>
                      <span> </span>{" "}
                      <span className="details"> &nbsp;{res.or_revenue}</span>{" "}
                    </b>
                  </div>*/}
                </div>
              </div>
            </div>
          </a>
        </div>
      </div>
    ),
    url:
      "http://" + PUBLIC_IP + 
      ":8080/index.html?input=" + res.dicom_filepath 
  }),
  innerClass: {
    title: "result-title",
    listItem: "result-item",
    list: "list-container",
    sortOptions: "sort-options",
    resultStats: "result-stats",
    resultsInfo: "result-list-info",
    poweredBy: "powered-by"
  }
};

export default resultComponent;