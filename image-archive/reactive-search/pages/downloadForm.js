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
      size: "lg"
    };

    this.toggle = this.toggle.bind(this);
  }

  toggle() {
    this.setState(prevState => ({
      modal: !prevState.modal
    }));
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


        <h4>To ensure that required approval is in place for your download, please submit a download request form.</h4>
        <p></p>

        <form>
        <FormGroup row>
          <Label for="exampleName" sm={2}>User Name</Label>
          <Col sm={10}>
            <Input type="name" name="User Name" id="exampleName" placeholder="" />
          </Col>
        </FormGroup>

        <FormGroup row>
          <Label for="exampleDate" sm={2}>Date</Label>
          <Col sm={10}>
            <Input type="date" name="date" id="date" placeholder="" /> 
          </Col>
        </FormGroup>
        <FormGroup row>
          <Label for="exampleSearch" sm={2}>Search</Label>
          <Col sm={10}>
            <Input type="search" name="Search" id="exampleSearch" placeholder="" />
          </Col>
        </FormGroup>


{/*        <FormGroup row>
          <Label for="exampleSearch" sm={2}>Image</Label>
          <Col sm={10}>
            <Input type="search" name="Image" id="Image" placeholder="Number of images" />
          </Col>
        </FormGroup>
        
        <FormGroup row>
          <Label for="exampleSearch" sm={2}>Exams</Label>
          <Col sm={10}>
            <Input type="search" name="Exams" id="Search" placeholder="Number of exams" />
          </Col>
        </FormGroup>

        <FormGroup row>
          <Label for="exampleSearch" sm={2}>Patients</Label>
          <Col sm={10}>
            <Input type="search" name="Patients" id="Patients" placeholder="Number of patients" />
          </Col>
        </FormGroup>*/}



        <Row form>
          <Col md={4}>
            <FormGroup>
              <Label for="exampleImages">Images</Label>
              <Input type="text" name="# Images" id="exampleImages" placeholder="Number of images"/>
            </FormGroup>
          </Col>
          <Col md={4}>
            <FormGroup>
              <Label for="exampleExams">Exams</Label>
              <Input type="text" name="# Exams" id="exampleExams" placeholder="Number of exams"/>
            </FormGroup>
          </Col>
          <Col md={4}>
            <FormGroup>
              <Label for="examplePatients">Patients</Label>
              <Input type="text" name="# Patients" id="examplePatients" placeholder="Number of patients"/>
            </FormGroup>  
          </Col>
        </Row>



        <FormGroup row>
          <Label for="exampleEmail" sm={2}>Email</Label>
          <Col sm={10}>
            <Input type="email" name="Email" id="exampleEmail" placeholder="" />
          </Col>
        </FormGroup>
        <FormGroup row>
          <Label for="examplePI" sm={2}>PI</Label>
          <Col sm={10}>
            <Input type="PI" name="PI" id="examplePI" placeholder="" />
          </Col>
        </FormGroup>
        <FormGroup row>
          <Label for="exampleUseCase" sm={2}>Use Case</Label>
          <Col sm={10}>
            <Input type="useCase" name="Use Case" id="exampleUseCase" placeholder="" />
          </Col>
        </FormGroup>


        <FormGroup row>
          <Label for="exampleText" sm={2}>Other Comments</Label>
          <Col sm={10}>
            <Input type="textarea" name="Other Comments" id="exampleText" />
          </Col>
        </FormGroup>
        
    <FormGroup check inline>
          <Label check>
            <Input type="checkbox" div className="checkbox-bigger"/> I agree to only use this data at SickKids for PI lead research approved by an REB study. I agree to report any sensitive PHI found to CCM for redaction.
          </Label>
        </FormGroup>
        <p></p>
        <Button onClick={this.submitForm} className="center-button"><span>
        <a className="submit-colour">Submit</a>
        </span></Button>

      <p></p>
      <h4>We will send you a download link once we process your request. For questions please contact <a className="sick-blue" href="https://github.com/aim-sk/aim-platform/wiki/Available-Fields-to-Search-By" target="_blank">daniel.snider@sickkids.ca</a>
      </h4>

        </form>
        </ModalBody>
        </Modal>
        </button>
    );
  }
}

export default DiannaExample;