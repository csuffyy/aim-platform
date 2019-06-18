import React, { Component } from "react";
import { DataSearch } from "@appbaseio/reactivesearch";
import { ButtonDropdown, DropdownToggle, DropdownMenu, DropdownItem } from 'reactstrap';
import ModalExample from "./Modal.jsx";
import DiannaExample from "./downloadForm.js"



function custQueryAllFields(value, props) {
  // Match everything if nothing specified
  if (value==='') {
      return {
        "query":{"match_all":{}}
      };
  }

  // Hanle possible leading "fields:" to allow user to specify what fields to look in for rest of search query
  var fields = null;
  if (value.indexOf("fields:")===0) {
    fields = value.split(" ")[0].replace('fields:','').split(","); // Use first part as the fields
    value = value.split(" ").slice(1).join(" "); // Use the other parts as the string query value
  }

  var query = {"query" : value };

  if (fields !== null) {
    query.fields = fields;
  }

  // Query String Query
  return {
    "allow_partial_search_results": false, // Does nothing, must be string-query parameter in URL. See: https://github.com/appbaseio/reactivesearch/issues/945#issuecomment-483427469
    "query": {
      "query_string" : query
    }
  };
}

var today = new Date();
var expiry = new Date(today.getTime() + 30 * 24 * 3600 * 1000); // plus 30 days
function setCookie(name, value)
{
  document.cookie=name + "=" + escape(value) + "; path=/; expires=" + expiry.toGMTString();
}

function deleteLoadingAnimation() {
  var elem = document.getElementById("loading_animation");
  if (elem) {
    elem.style.height = '0px';
  }
}
var queryError;

const components = {
  dataSearch: {
    componentId: "mainSearch",
    debounce: 1000,
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
    this.beforeValueChange = this.beforeValueChange.bind(this);
    // components.dataSearch.beforeValueChange = this.beforeValueChange; // NOTE THIS IS NOT USED BECAUSE: https://github.com/appbaseio/reactivesearch/issues/945#issuecomment-483427469  
    this.LogOut = this.LogOut.bind(this);
    this.todayDate = this.todayDate.bind(this);
    this.toggle = this.toggle.bind(this);
    this.state = {
      dropdownOpen: false,
      queryError: false
    };

  }

  todayDate() {
    // today_str = (new Date()).format("yyyy/mm/dd");
    console.log(today_str);
    // document.getElementById('date').value = today_str;
  }

  // NOTE THIS IS NOT USED BECAUSE: https://github.com/appbaseio/reactivesearch/issues/945#issuecomment-483427469
  beforeValueChange(value) {
    return new Promise((resolve, reject) => {
      // console.log(value)
      // Validate Custom Query
      var elem = document.getElementsByClassName("search-bar");
      // if (Math.round(Math.random()))
      var validationError = false; // TODO: check with ES to validate the string query
      if (validationError)
      { 
        this.state.queryError = true;
        if (elem) {
          elem[0].style.border = '2px solid #f95959';
        }
        setTimeout(deleteLoadingAnimation, 1111);
        console.log('error in string query');
      } else {
        if (elem) {
          elem[0].style.border = '2px solid #86ddf8';
        }
        this.state.queryError = false;
      }
      resolve();
    })
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
                <ModalExample lastQuery={this.props.lastquery} buttonLabel="Help"/>
              
                <DiannaExample lastQuery={this.props.lastquery} buttonLabel="Download" />
                <button type="button" className="btn btn-secondary app-button" onClick={this.LogOut}>Logout</button>
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
