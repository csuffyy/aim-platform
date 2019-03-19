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
import resultComponent from "./resultComponent.jsx";
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

  resultCard: resultComponent
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
    // console.log(this.state.height);
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
    // console.log('updatePredicate');
    this.setState({ isDesktop: window.innerWidth > 1450 });
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


              <ResultCard {...resultComponent} />
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
