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


const components = {
  settings: {
    app: ELASTIC_INDEX,
    url: "http://" + ELASTIC_IP + ":" + ELASTIC_PORT + "/",
    // credentials: "abcdef123:abcdef12-ab12-ab12-ab12-abcdef123456",
    headers: {
        // secret: 'reactivesearch-is-awesome',
        'X-Requested-With': 'bar' // Not arbitrary headers are not allowed see whitelist in elasticsearch.yml
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
    loader: "Loading ..."
  },

  resultCard: {
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
    size: 12,
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
                    class="btn btn-dark"
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
  }
};

function AddToCollection(e, res) {
  console.log(e);
  console.log(res);
  e.preventDefault();
  // CALL API
}

class Main extends Component {
  constructor(props) {
    super(props);

    this.state = {
      isClicked: false,
      message: "🔬Show Filters"
    };
  }

  handleClick() {
    console.log("handleClick");
    console.log(this);
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
    console.log('token: ' + token);
    console.log('AUTH_TOKEN: ' + AUTH_TOKEN);

    // Set a header
    // res.setHeader('X-Foo', 'bar');

    // Redirect to login if no token
    if (token !== AUTH_TOKEN) {
      console.log('invalid token')
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
      )
    };
  }

  render() {
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
