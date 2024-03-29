import React, { Component } from "react";
// import resultComponent from "./resultComponent.jsx";
// import Main, {myvar} from "./index.jsx";
import {
  removeComponent,
  updateHits
} from "@appbaseio/reactivecore/lib/actions";

import {
  ResultCard,
  MultiDataList,
  RangeSlider,
  TagCloud,
  DateRange,
  MultiList,
  SingleRange
} from "@appbaseio/reactivesearch";



const components = {
  multiListModality: {
    componentId: "modality-list",
    dataField: "Modality.raw",
    className: "modality-filter",
    size: 20,
    sortBy: "count",
    queryFormat: "or",
    selectAllLabel: "All Modalities",
    showCheckbox: true,
    showCount: true,
    showSearch: true,
    placeholder: "Search for a Modality",
    react: {
      and: [
        "mainSearch",
        "results",
        "gender-list",
        "bodypart-list",
        "age-slider",
        "acquisitiondate-range",
        "tagCloud"
      ]
    },
    showFilter: true,
    filterLabel: "Modality",
    URLParams: false,
    innerClass: {
      label: "list-item",
      input: "list-input"
    }
  },

  multiListGender: {
    componentId: "gender-list",
    dataField: "PatientSex.raw",
    className: "gender-filter",
    size: 20,
    sortBy: "count",
    queryFormat: "or",
    selectAllLabel: "All Genders",
    showCheckbox: true,
    showCount: true,
    showSearch: false,
    placeholder: "Search for a Gender",
    react: {
      and: [
        "mainSearch",
        "results",
        "modality-list",
        "bodypart-list",
        "age-slider",
        "acquisitiondate-range",
        "tagCloud"
      ]
    },
    showFilter: true,
    filterLabel: "Gender",
    URLParams: false,
    innerClass: {
      label: "list-item",
      input: "list-input"
    }
  },
  multiListBodyPart: {
    componentId: "bodypart-list",
    dataField: "BodyPartExamined.raw",
    className: "bodypart-filter",
    size: 100,
    sortBy: "count",
    queryFormat: "or",
    selectAllLabel: "All Body Parts",
    showCheckbox: true,
    showCount: true,
    showSearch: true,
    placeholder: "Search for a Body Part",
    react: {
      and: [
        "mainSearch",
        "results",
        "modality-list",
        "gender-list",
        "age-slider",
        "acquisitiondate-range",
        "tagCloud"
      ]
    },
    showFilter: true,
    filterLabel: "Body Part",
    URLParams: false,
    innerClass: {
      label: "list-item",
      input: "list-input"
    }
  },
  rangeSliderAge: {
    componentId: "age-slider",
    dataField: "PatientAgeInt",
    className: "age-filter",
    filterLabel: "Age",
    range: {
      start: 0,
      end: 30
    },
    rangeLabels: {
      start: "0",
      end: "30"
    },
    react: {
      and: [
        "mainSearch",
        "results",
        "modality-list",
        "gender-list",
        "bodypart-list",
        "acquisitiondate-range",
        "tagCloud"
      ]
    }
  },
  dateRangeAcquisition: {
    componentId: "acquisitiondate-range",
    dataField: "AcquisitionDate.keyword",
    queryFormat: "date",
    className: "acquisitiondate-filter"
  }
};

class Leftbar extends Component {

  state = {
      date: new Date(),
    }

    onChange = date => this.setState({ date })

  constructor() {
    super();
    this.state = { isChecked: false };
    this.handleChecked = this.handleChecked.bind(this); // set this, because you need get methods from CheckBox
  }

  handleChecked() {
    this.setState({ isChecked: !this.state.isChecked });
  }

  static async getInitialProps() {
    return {
      store: await initReactivesearch(
        [
          {
            ...components.multiListModality,
            type: "MultiList",
            source: MultiList
          },
          {
            ...components.multiListBodyPart,
            type: "MultiList",
            source: MultiList
          },
          {
            ...components.multiListGender,
            type: "MultiList",
            source: MultiList
          },
          {
            ...components.dateRangeAcquisition,
            type: "DateRange",
            source: DateRange
          },
          {
            ...components.rangeSliderAge,
            type: "RangeSlider",
            source: RangeSlider
          }
        ],
        null
      )
    };
  }

  render() {
    // var show_rangeSliderAge;
    // // console.log(this)
    // if (this.state.isChecked) {
    //   myvar("checked")
    //   show_rangeSliderAge = "checked";
    //   // components.multiListBodyPart.componentId = 'nope';
    //   components.rangeSliderAge.componentId = 'age-slider';
    //   components.rangeSliderAge.dataField = "PatientAgeInt";
    //   // components.multiListBodyPart.componentId = 'nope';
    //   // components.multiListBodyPart.componentId = 'bodypart-list';
    //   // resultComponent.key = 'results';
    //   // resultComponent.componentId = 'nopes';
    //   // resultComponent.componentId = 'results';
    //   // resultComponent.react = {
    //   //   and: [
    //   //     "mainSearch",
    //   //     "modality-list",
    //   //     "gender-list",
    //   //     "bodypart-list",
    //   //     "age-slider",
    //   //     "age-slider2",
    //   //     "acquisitiondate-range",
    //   //     "tagCloud"
    //   //   ]
    //   // };
    //   // console.log(resultComponent.react);
    //   // console.log(myvar); console.log(myvar);
    // } else {
    //   myvar("unchecked")

    //   // console.log(myvar); console.log(myvar);
    //   components.rangeSliderAge.componentId = 'nope';
    //   components.rangeSliderAge.dataField = "";
    //   show_rangeSliderAge = "unchecked";
    //   // console.log(resultComponent.react);
    //   // resultComponent.react = {
    //   //   and: [
    //   //     "mainSearch",
    //   //     "modality-list",
    //   //     "gender-list",
    //   //     "bodypart-list",
    //   //     "acquisitiondate-range",
    //   //     "tagCloud"
    //   //   ]
    //   // };


    //   // key
    //   // componentId
    //   // multiListBodyPart

    //   // updateHits()
    //   // removeComponent(...components.dateRangeAcquisition)
    //   // this.forceUpdate();
    //   // console.log(document)
    //   // var elem = document.getElementById('ceohuao');
    //   // elem.parentNode.removeChild(elem);
    // }

    return (
      <div className={this.props.isClicked ? "left-bar-optional" : "left-bar"}>
        <div className="filter-heading center">
          <b>
            {" "}
            <i className="fa fa-camera" /> Modality{" "}
          </b>
        </div>

        <MultiList {...components.multiListModality} />

        <hr className="blue" />

        <div className="filter-heading center">
          <b>
            {" "}
            <i className="fa fa-user" /> Body Part{" "}
          </b>
        </div>

        <MultiList {...components.multiListBodyPart} />

        <hr className="blue" />

        <div className="filter-heading center">
          <b>
            {" "}
            <i className="fa fa-transgender" /> Gender{" "}
          </b>
        </div>

        <MultiList {...components.multiListGender} />

        <hr className="blue" />

        <div className="filter-heading center">
          <b>
            <i className="fa fa-address-card" /> Patient Age
          </b>
        </div>

        <RangeSlider {...components.rangeSliderAge} />

        <div style={{height:'6px'}}></div>


        <hr className="blue" />

        <div className="filter-heading center" >
          <b>
            {" "}
            <i className="fa fa-calendar" /> Acquisition Date{" "}
          </b>
        </div>

        <DateRange {...components.dateRangeAcquisition} />
              </div>
    );
  }
}
export default Leftbar;
