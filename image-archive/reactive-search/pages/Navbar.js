import React, { Component } from "react";
import { DataSearch } from "@appbaseio/reactivesearch";

// function custQuery(value, props) {
// COLON DELIMITED SEARCH
// Examle FIELD:SEARCH
//   if (value.length == 0) {
//     return;
//   }
//   if (!value.includes(":")) {
//     return;
//   }

//   var res = value.split(":");
//   var field = res[0];
//   var search = res[1];
//   var query = { [field]: search };

//   return {
//     match: query
//   };
// }

function custQueryAllFields(value, props) {
  return {
    query: { multi_match: { query: value } }
  };
}

// function custQueryAllDocuments(value, props) {
//   return {
//     "query":{"match_all":{}}
//   };
// }

const components = {
  dataSearch: {
    componentId: "mainSearch",
    // dataField: ["descriptions"],
    // dataField: ["StudyDescription","ReasonForStudy","SeriesDescription","StudyComments"],
    customQuery: custQueryAllFields,
    categoryField: "title",
    className: "search-bar",
    queryFormat: "and",
    placeholder: "Search for images...",
    iconPosition: "left",
    autosuggest: false,
    filterLabel: "search",
    highlight: true
  }
};

class Navbar extends Component {
  static async getInitialProps() {
    return {
      store: await initReactivesearch(
        [
          {
            ...components.datasearch,
            type: "DataSearch",
            source: DataSearch
          }
        ],
        null
      )
    };
  }
  render() {
    return (
      <div className="navbar">
        <div className="logo-container">
          <img
            className="app-logo"
            src="/static/sickkids.png"
            alt="ImageArchive"
          />
        </div>

        <div className="search-container">
          <DataSearch {...components.dataSearch} />
        </div>
      </div>
    );
  }
}
export default Navbar;
