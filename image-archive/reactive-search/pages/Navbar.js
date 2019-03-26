import React, { Component } from "react";
import { DataSearch } from "@appbaseio/reactivesearch";
import { ButtonDropdown, DropdownToggle, DropdownMenu, DropdownItem } from 'reactstrap';


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
  // console.log(props)
  // console.log(value)
  // console.log(value===undefined)
  // console.log(value==='')
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
    dataField: [],
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


    this.toggle = this.toggle.bind(this);
    this.state = {
      dropdownOpen: false
    };

  }

  toggle() {
    this.setState({
      dropdownOpen: !this.state.dropdownOpen
    });
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
        <div className="wrapper">
          <aside className="aside aside-logo">
            <div className="container">
              <div className="row">
                <div style={{float: "left"}}>
                  <img
                    className="app-logo"
                    src="/static/sickkids.png"
                    alt="ImageArchive"
                  />
                </div>
              </div>
              <div className="row">

                <ButtonDropdown isOpen={this.state.dropdownOpen} toggle={this.toggle}>
                  <DropdownToggle caret className='data-selector-button'>
                    <h3 className="header-text">
                      Diagnostic Imaging Archive
                    </h3>

                  </DropdownToggle>
                  <DropdownMenu>
                    {/* <DropdownItem header>Header</DropdownItem> */}
                    <DropdownItem disabled >
                      <h3 className="header-text">
                      Stroke Lab Research Study
                      </h3>
                    </DropdownItem>
                    {/*
                    <DropdownItem disabled >
                      <h3 className="header-text">
                      Radiology Text Reports
                      </h3>
                     </DropdownItem>
                   */}
                    {/*
                     <DropdownItem divider />
                   */}
                    {/* <DropdownItem disabled>
                      <h3 className="header-text">
                      Another
                      </h3>
                     </DropdownItem> */}
                  </DropdownMenu>
                </ButtonDropdown>
              </div>
            </div>
          </aside>




          <aside className="aside aside-buttons">
            <div className="btn-container">
              <div className="row">
                <div className="col-sm">
              <div>
                            <span className="header-support-text">
                <a className="login-footer-link" href="mailto:daniel.snider@sickkids.ca?subject=Diagnostic Imaging Archive Support" target="_blank">Support</a> Provided by <a className="login-footer-link" href="https://ccm.sickkids.ca/" target="_blank">The Centre for Computational Medicine</a>
              </span>
              </div>
                </div>
              </div>
              <div className="row btn-group">
              <button type="button" className="btn btn-secondary app-button disabled">Collections</button>
              <button type="button" className="btn btn-secondary app-button disabled">Download</button>
              <button type="button" className="btn btn-secondary app-button" onClick={this.LogOut}>Log Out</button>
              </div>
            </div>
           
          </aside>

          <footer className="header-footer">
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
