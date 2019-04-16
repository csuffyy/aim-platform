import React, { Component } from "react";
import {
  ReactiveBase,
  TagCloud,
  SelectedFilters,
  ResultCard
} from "@appbaseio/reactivesearch";
var cookie = require('cookie');
import Navbar from "./Navbar.js";
import Leftbar from "./Leftbar.js";
import initReactivesearch from "@appbaseio/reactivesearch/lib/server";
import "./index.css";

import getConfig from 'next/config';
const {publicRuntimeConfig} = getConfig();
const {PUBLIC_IP} = publicRuntimeConfig;
const {ELASTIC_URL} = publicRuntimeConfig;
const {ELASTIC_INDEX} = publicRuntimeConfig;
const {AUTH_TOKEN} = publicRuntimeConfig;
const {FILESERVER_TOKEN} = publicRuntimeConfig;
const {STATIC_WEBSERVER_URL} = publicRuntimeConfig;
const {DWV_URL} = publicRuntimeConfig;

if (AUTH_TOKEN === undefined) {
  throw new Error('AUTH_TOKEN is undefined');
}

var FILESERVER_SECRET = '';
var FILESERVER_SECRET_DCM = '';
if (FILESERVER_TOKEN != '') {
  FILESERVER_SECRET = '-0TO0-' + AUTH_TOKEN
  FILESERVER_SECRET_DCM = '-0TO0-' + AUTH_TOKEN + '.dcm'
}

function redSearchBar() {
  if (typeof window !== 'undefined') {
    var elem = document.getElementsByClassName("search-bar");
    if (elem) {
      elem[0].style.border = '2px solid #f95959';
    }
  }
}

const components = {
  settings: {
    app: ELASTIC_INDEX,
    url: ELASTIC_URL,
    // credentials: "abcdef123:abcdef12-ab12-ab12-ab12-abcdef123456", // DO NOT DELETE THIS COMMENT. ReactiveSearch will break =X!
    headers: {
        'X-Requested-With': AUTH_TOKEN // arbitrary headers are not allowed see whitelist in elasticsearch.yml
    },
    theme: {
      typography: {
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Noto Sans", "Ubuntu", "Droid Sans", "Helvetica Neue", sans-serif',
        fontSize: "16px"
      },
      colors: {
        textColor: "#fff",
        backgroundColor: "#212121",
        primaryTextColor: "#fff",
        primaryColor: "#2196F3",
        titleColor: "#fff",
        alertColor: "#d9534f",
        borderColor: "#666"
      }
    }
  },
  selectedFilters: {
    showClearAll: true,
    clearAllLabel: "Clear filters"
  },
  tagCloudDescription: {
    componentId: "tagCloud",
    dataField: "descriptions.raw",
    title: "",
    size: 200,
    showCount: true,
    multiSelect: true,
    queryFormat: "or",
    react: {
      and: [
        "mainSearch",
        "results",
        "gender-list",
        "bodypart-list",
        "age-slider",
        "acquisitiondate-range"
      ]
    },
    showFilter: true,
    filterLabel: "Description",
    URLParams: false,
    loader: ""
  },

  resultCard: {
    componentId: "results",
    // onQueryChange: onQueryChange,
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
    loader: <object id='loading_animation' type="image/svg+xml" data="static/ekg.svg">Your browser does not support SVG</object>,
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
    // onNoResults: 'NO RESULTS OK?',
    onError: function(res) {
      console.log('onError');
      console.log(res);
      setTimeout(redSearchBar, 111);
  },
    onData:   function(res) {
      // setBlueSearchBar incase it was red because of an error
      if (typeof window !== 'undefined') {
        var elem = document.getElementsByClassName("search-bar");
        if (elem) {
          elem[0].style.border = '2px solid #86ddf8';
        }
      }

    return {
      description: (
        <div className="main-description">
          <div className="ih-item square effect6 top_to_bottom">

            <a
              target="#"
              href={
                DWV_URL + 
                "index.html?input=" + 
                STATIC_WEBSERVER_URL +
                res.dicom_relativepath + FILESERVER_SECRET_DCM
              }
            >

              <div className="img">
                <img
                  src={STATIC_WEBSERVER_URL + res.thumbnail_filepath + FILESERVER_SECRET}
                  alt={res.original_title}
                  className="result-image"
                />
                {/* Example src:
                http://192.168.136.128:3000/static/thumbnails/CT-MONO2-16-ankle.dcm.png */}
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
        DWV_URL + 
        "index.html?input=" + 
        STATIC_WEBSERVER_URL +
        res.dicom_relativepath + FILESERVER_SECRET_DCM
    }},
    innerClass: {
      title: "result-title",
      listItem: "result-item",
      list: "list-container",
      sortOptions: "sort-options",
      resultStats: "result-stats",
      resultsInfo: "result-list-info",
      poweredBy: "powered-by"
    }
  }
};

function AddToCollection(e, res) {
  // console.log(e);
  // console.log(res);
  e.preventDefault();
  // CALL API
}

class Main extends Component {
  constructor(props) {
    super(props);

    this.state = {
      isClicked: false,
      message: "🔬Show Filters",
      isDesktop: false,
      height: 0, 
      width: 0,
    };

    this.updatePredicate = this.updatePredicate.bind(this);
    this.updateDimensions = this.updateDimensions.bind(this);
  }

  componentDidMount() {
    // Additionally I could have just used an arrow function for the binding `this` to the component...
    window.addEventListener("resize", this.updateDimensions);
    this.updatePredicate();
    window.addEventListener("resize", this.updatePredicate);
    this.updateDimensions()
  }
  updateDimensions() {
    this.setState({
      height: window.innerHeight, 
      width: window.innerWidth
    });
    const divWidth = document.getElementsByClassName('Result_card')[0].clientWidth;
    components.resultCard.size = 4 * Math.floor((-150 + divWidth) / 250);
  }

  componentWillUnmount() {
    window.removeEventListener("resize", this.updateDimensions);
    window.removeEventListener("resize", this.updatePredicate);
  }

  updatePredicate() {
    this.setState({ isDesktop: window.innerWidth > 1450 });
  }


  handleClick() {
    this.setState({
      isClicked: !this.state.isClicked,
      message: this.state.isClicked ? "🔬 Show Filters" : "🎬 Show Images"
    });
  }

  static async getInitialProps({res, req}) {
    // Parse the cookies on the request
    var cookies = cookie.parse(req.headers.cookie || '');
    
    // Get the visitor name set in the cookie
    var token = cookies.token;

    // Set a header
    // res.setHeader('X-Foo', 'bar');

    // Redirect to login if no token
    if (token !== AUTH_TOKEN) {
      res.writeHead(302, {
        Location: 'login'
      })
      res.end() // load nothing else
    }

    return {
      store: await initReactivesearch(
        [
          {
            ...components.selectedFilters,
            type: "SelectedFilters",
            source: SelectedFilters
          },
          {
            ...components.resultCard,
            type: "ResultCard",
            source: ResultCard
          }
        ],
        null,
        components.settings
      ),
    };
  }

  render() {
    const isDesktop = this.state.isDesktop;
    return (
      <div className="main-container">
        <ReactiveBase {...components.settings} initialState={this.props.store}>
          <Navbar />

          <div className="sub-container">
            <Leftbar isClicked={this.state.isClicked} />

            <div
              className={
                this.state.isClicked
                  ? "result-container-optional"
                  : "result-container"
              }
            >
              <SelectedFilters {...components.selectedFilters} />


{/*              <div>
                {isDesktop ? (
                  <div>I show on 1451px or higher</div>
                ) : (
                  <div>I show on 1450px or lower</div>
                )}
              </div>
              <h3>
                Window width: {this.state.width} and height: {this.state.height} Number of Results: {components.resultCard.size}
              </h3>*/}


              <ResultCard {...components.resultCard} />
            </div>

            <button
              className="toggle-button"
              onClick={this.handleClick.bind(this)}
            >
              {this.state.message}
            </button>
          </div>

          <div className="bottom-bar">
            <div className="filter-heading center">
              <b>
                {" "}
                <i className="fa fa-cloud" /> Tag Cloud{" "}
              </b>
            </div>

            <TagCloud {...components.tagCloudDescription} />
          </div>
        </ReactiveBase>

      </div>
    );
  }
}

export default Main;
// export function myvar(state){
//   if (state === 'checked') {
//     components.resultCard.componentId = 'nopes';
//     components.resultCard.componentId = 'results';
//     components.resultCard.react = {
//       and: [
//         "mainSearch",
//         "modality-list",
//         "gender-list",
//         "bodypart-list",
//         "age-slider",
//         "acquisitiondate-range",
//         "tagCloud"
//       ]
//     };
//     console.log(components.resultCard.react);
//     console.log(state);
//   } else {
//     components.resultCard.componentId = 'nopes';
//     components.resultCard.componentId = 'results';


//     components.resultCard.react = {
//       and: [
//         "mainSearch",
//         "modality-list",
//         "gender-list",
//         "bodypart-list",
//         "acquisitiondate-range",
//         "tagCloud"
//       ]
//     };
//     console.log(components.resultCard.react);
//     console.log(state);

//   }
// };
