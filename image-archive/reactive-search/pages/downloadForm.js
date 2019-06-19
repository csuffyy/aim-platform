import React, { Component } from "react";
import { DataSearch } from "@appbaseio/reactivesearch";
import { Button, Modal, ModalHeader, ModalBody, ModalFooter, Table, Col, Row, Form, FormGroup, Label, Input, FormText } from 'reactstrap';

const components = {
  dataSearch: {
    componentId: "search",
    debounce: 1000,
    // dataField: ["descriptions"],
    // dataField: ["StudyDescription","ReasonForStudy","SeriesDescription","StudyComments"],
    dataField: [],
    categoryField: "title",
    className: "",
    queryFormat: "and",
    placeholder: " ",
    iconPosition: "left",
    autosuggest: false,
    filterLabel: " ",
    highlight: true
  }
};

class DiannaExample extends Component {
    constructor(props) {
    super(props);
    this.submitForm = this.submitForm.bind(this);
    this.state = {
      modal: false,
      size: "lg",
      images: 0,
      exams: 0,
      patients: 0,
      search: "",
      exampleSearch_style: "",
      examplePatient_display: "",
      exampleExam_display: "",
      exampleColour: "",
      date: this.getDate(),
      // results: this.getResults()
    };

    this.toggle = this.toggle.bind(this);
  }

  toggle() {
    this.setState(prevState => ({
      modal: !prevState.modal
    }));

    // Populate form fields
    var _div2 = document.getElementsByClassName('css-148lm57')[0];
    var split_div2 = _div2.innerHTML.split(" ");
    if (split_div2[1]) { //check that some was searched
        split_div2 = split_div2[1].split("<");
        this.state.search = split_div2[0];
    }
    else{ //nothing was searched, so entire image set returned
        this.state.search = "Entire Image Set";
    }

    if (document.getElementsByClassName('result-stats')[0]) { //check image count
        var _div = document.getElementsByClassName('result-stats')[0];
        var split_div = _div.innerHTML.split(" ");
        this.state.images = split_div[0];
        this.state.exampleSearch_style ='0px solid grey'
    }
    else { //no images found so red box is created
        this.state.search = "No results found, please alter your search.";
        this.state.images = 0;
        this.state.exams = 0;
        this.state.patients = 0;
        this.state.exampleSearch_style ='2px solid #f95959';
    }

    if (!_div.innerHTML.includes('patient')) { //patients are not present in the query results
        this.state.examplePatient_display = 'none';
    }
    if (!_div.innerHTML.includes('exam')) { //exams are not present in query results
        this.state.exampleExam_display = 'none';
    }

  }

  getDate() {
    var today = new Date();
    var dd = today.getDate();

    var mm = today.getMonth()+1; 
    var yyyy = today.getFullYear();
    if(dd<10) 
    {
        dd='0'+dd;
    } 

    if(mm<10) 
    {
        mm='0'+mm;
    } 
    today = yyyy+'-'+mm+'-'+dd;
    return today;
  }

  submitForm(event) {

    var name=document.getElementById("exampleName").value;
    var date=document.getElementById("exampleDate").value;
    var search=document.getElementById("exampleSearch").value;
    var numImages=document.getElementById("exampleImages").value;
    var numExams=document.getElementById("exampleExams").value;
    var numPatients=document.getElementById("examplePatients").value;
    var PI=document.getElementById("examplePI").value;
    var email=document.getElementById("exampleEmail").value;
    var useCase=document.getElementById("exampleUseCase").value;
    var comments=document.getElementById("exampleText").value;

    var comment_split = comments.split("\n");
    comments = comment_split.join("%0D%0A");

    window.location.href = "mailto:daniel.snider@sickkids.ca?subject=Diagnostic Imaging Archive Document Request&body=User: " + name + "%0D%0A%0D%0A Date: " + date +"%0D%0A%0D%0A Search: " + search + "%0D%0A%0D%0A Number of Images: " + numImages + " %0D%0A%0D%0A Number of Exams: " + numExams + "%0D%0A%0D%0A Number of Patients: " + numPatients + "%0D%0A%0D%0A Email: " + email + "%0D%0A%0D%0A PI: " + PI + "%0D%0A%0D%0A Use Case: " + useCase + "%0D%0A%0D%0A Other Comments: " + comments + "%0D%0A%0D%0A";
  }

  getResults() {
    console.log('_div');

    if (typeof window !== 'undefined') {

    }
    return 
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
        <button type="button" className="btn btn-secondary app-button" onClick={this.toggle}>{this.props.buttonLabel}
        <Modal isOpen={this.state.modal} toggle={this.toggle} className="{this.props.className} app-modal " size="lg">
          <ModalHeader toggle={this.toggle}>
            <div className="filter-heading center" style={{margin:"0px"}}>
              <b>
                {" "}
                <i className="fa fa-download" /> Download{" "}
              </b>
            </div>
            </ModalHeader>

        <ModalBody>
        <h3>
          Download Request Form
        </h3>


        <p>
        To ensure that required approval is in place for your download, please submit a download request form:
        </p>

        <form style={{padding:'0 20px'}}>
          <div style={{padding:'0 30px 0 0'}}>

        <FormGroup row>
          <Label for="exampleSearch" sm={3}>Search</Label>
          <Col sm={9}>
            <Input type="search" name="Search" id="exampleSearch" value={this.state.search} style={{border: this.state.exampleSearch_style}} disabled/>{this.state.results}
          </Col>
        </FormGroup>

        <FormGroup row>
          <Label for="exampleSearch" sm={3}>Total</Label>
          <Col md={3}>
              <Label for="exampleImages">Images</Label>
              <Input type="text" name="# Images" id="exampleImages" value={this.state.images} placeholder="Number of images" style={{border: this.state.exampleSearch_style}} disabled/>
          </Col>
          <Col md={3}>
              <Label for="exampleExams" style={{display: this.state.exampleExam_display}}>Exams</Label>
              <Input type="text" name="# Exams" id="exampleExams" value={this.state.exams} placeholder="Number of exams" style={{border: this.state.exampleSearch_style, display:this.state.exampleExam_display}} disabled/>
          </Col>
          <Col md={3}>
              <Label for="examplePatients" style={{display: this.state.examplePatient_display}}>Patients</Label>
              <Input type="text" name="# Patients" id="examplePatients" value={this.state.exams}placeholder="Number of patients" style={{border: this.state.exampleSearch_style, display:this.state.examplePatient_display}} disabled/>
          </Col>
        </FormGroup>


        <FormGroup row>
          <Label for="exampleName" sm={3}>Name</Label>
          <Col sm={9}>
            <Input type="name" name="Name" id="exampleName" placeholder="" />
          </Col>
        </FormGroup>


        <FormGroup row>
          <Label for="exampleEmail" sm={3}>Email</Label>
          <Col sm={9}>
            <Input type="email" name="Email" id="exampleEmail" placeholder="" />
          </Col>
        </FormGroup>

        <FormGroup row>
          <Label for="exampleDate" sm={3}>Date</Label>
          <Col sm={9}>
          <Input type="date" name="date" id="exampleDate" value={this.state.date} /> 

          </Col>
        </FormGroup>

        <FormGroup row>
          <Label for="examplePI" sm={3}>PI</Label>
          <Col sm={9}>
            <Input type="PI" name="PI" id="examplePI" placeholder="" />
          </Col>
        </FormGroup>
        <FormGroup row>
          <Label for="exampleUseCase" sm={3}>Use Case</Label>
          <Col sm={9}>
            <Input type="useCase" name="Use Case" id="exampleUseCase" placeholder="" />
          </Col>
        </FormGroup>


        <FormGroup row>
          <Label for="exampleText" sm={3}>Other Comments</Label>
          <Col sm={9}>
            <Input type="textarea" name="Other Comments" id="exampleText" />
          </Col>
        </FormGroup>
      </div>
        
    <FormGroup check inline>
          <Label check>
            <Input type="checkbox" div className="checkbox-bigger"/> <div style={{paddingLeft:"70px"}}> I agree to only use this data at SickKids for PI lead research approved by an REB study and to report any PHI found to CCM.</div>
          </Label>
        </FormGroup>
        <p></p>
        <Button onClick={this.submitForm} className="center-button"><span>
        <a className="submit-colour">Submit</a>
        </span></Button>

      <p></p>

      <h4 style={{marginTop:'15px'}}>Once we process your request we will send you download instructions. For questions please contact <a className="sick-blue" href="mailto:daniel.snider@sickkids.ca?subject=Diagnostic Imaging Archive Support" target="_blank">Support</a>. </h4>

        </form>

        </ModalBody>
        </Modal>
        </button>
    );
  }
}

export default DiannaExample;