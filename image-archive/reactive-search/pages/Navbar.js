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
  console.log(props)
  console.log(value)
  console.log(value===undefined)
  console.log(value==='')
  // if (value==='') {
  //   value = undefined;
  // }

  return {
    query: { multi_match: { query: value } }
  };
}

// function custQueryAllFields(value, props) {
//   return {
//     "query":{"match_all":{}}
//   };
// }

var today = new Date();
var expiry = new Date(today.getTime() + 30 * 24 * 3600 * 1000); // plus 30 days
function setCookie(name, value)
{
  document.cookie=name + "=" + escape(value) + "; path=/; expires=" + expiry.toGMTString();
}


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
  constructor(props) {
    super(props);
    this.LogOut = this.LogOut.bind(this);
  }

  LogOut(event) {
    setCookie('token','');
    location.reload();
  }

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
        <div class="wrapper">
          <aside class="aside aside-logo">
            <div style={{float: "left"}}>
              <img
                className="app-logo"
                src="/static/sickkids.png"
                alt="ImageArchive"
              />
            </div>
          </aside>

          <article class="main">
              <h3 className="header-text">
                Diagnostic Image Archive
              </h3>
              <span className="header-support-text">
                <a className="login-footer-link" href="mailto:daniel.snider@sickkids.ca?subject=Diagnostic Image Archive Support" target="_blank">Support</a> Provided by <a className="login-footer-link" href="https://ccm.sickkids.ca/" target="_blank">CCM</a>
              </span>
          </article>

          <aside class="aside aside-buttons">
           
              <button type="button" className="btn btn-secondary app-button">Collections</button>
              <button type="button" className="btn btn-secondary app-button">Download</button>
              <button type="button" className="btn btn-secondary app-button" onClick={this.LogOut}>Log Out</button>
          </aside>

          <footer class="header-footer">
            <div className="search-container">
            <DataSearch {...components.dataSearch} />
            </div>
          </footer>
        </div>

      </div>
    );
  }
}
export default Navbar;
