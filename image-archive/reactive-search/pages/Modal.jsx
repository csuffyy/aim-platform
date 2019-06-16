/* eslint react/no-multi-comp: 0, react/prop-types: 0 */

import React from 'react';
import { Button, Modal, ModalHeader, ModalBody, ModalFooter, Table} from 'reactstrap';

class ModalExample extends React.Component {
  constructor(props) {
    super(props);
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

  render() {
    return (
        <button type="button" className="btn btn-secondary app-button" onClick={this.toggle}>{this.props.buttonLabel}
        <Modal isOpen={this.state.modal} toggle={this.toggle} className="{this.props.className} app-modal " size="lg">
          <ModalHeader toggle={this.toggle}>
            <div className="filter-heading center" style={{margin:"0px"}}>
              <b>
                {" "}
                <i className="fa fa-question-circle" /> Help{" "}
              </b>
            </div>

          </ModalHeader>
          <ModalBody>

            <p></p>
            <h3>
              Search Examples
            </h3>
            <p></p>

            This archive's search box allows queries to be entered that follow the "String Query" syntax, which is a mini-language in Elasticsearch. Below we summarize possible searchers that can be performed. For more info visit the <a className="sick-blue" href="https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html#query-string-syntax" target="_blank">ElasticSearch docs</a>.
            <p></p>

      <Table>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Boolean
            </th>
            <td className="blue-line"> <pre className="app-pre">
            (quick OR brown) AND fox
            </pre> </td>
            <td className="blue-line">
            Multiple terms or clauses can be grouped together like "quick OR brown" with parent­heses, to form sub-qu­eries
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Search Within One Field
            </th>
            <td className="blue-line"> <pre className="app-pre">
            statu­s:a­ctive
            </pre> </td>
            <td className="blue-line">
            Field "­sta­tus­" contains "­act­ive­"
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Search Within Multiple Fields
            </th>
            <td className="blue-line"> <pre className="app-pre">
            fields:[a,b,c]
            </pre> </td>
            <td className="blue-line">
            "a", "b" and "c" will be the only fields searched. No spaces allowed
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            PatientID
            </th>
            <td className="blue-line"> <pre className="app-pre">
            fields:PatientID ID1 ID2
            </pre> </td>
            <td className="blue-line">
            Fast PatientID searching. Max 1024 IDs at a time
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            AccessionNumber
            </th>
            <td className="blue-line"> <pre className="app-pre">
            fields:AccessionNumber ID1 ID2
            </pre> </td>
            <td className="blue-line">
            Fast AccessionNumber searching
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Patient Age
            </th>
            <td className="blue-line"> <pre className="app-pre">
            PatientAgeInt &#60; 8
            </pre> </td>
            <td className="blue-line">
            Search by patient age
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Regular Expression
            </th>
            <td className="blue-line"> <pre className="app-pre">
            name:/joh?n(ath[oa]n)/
            </pre> </td>
            <td className="blue-line">
            More information about <a className="sick-blue" href="https://medium.com/factory-mind/regex-tutorial-a-simple-cheatsheet-by-examples-649dc1c3f285">regex</a>
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Wildcard
            </th>
            <td className="blue-line"> <pre className="app-pre">
            qu?ck bro*
            </pre> </td>
            <td className="blue-line">
            "­?" to replace a single character, and "­*" to replace zero or more characters
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Missing Field Value
            </th>
            <td className="blue-line"> <pre className="app-pre">
            _miss­ing­_:t­itle
            </pre> </td>
            <td className="blue-line">
            Field "­tit­le" has no value
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Fuzzy
            </th>
            <td className="blue-line"> <pre className="app-pre">
            quikc~
            </pre> </td>
            <td className="blue-line">
            More information about <a className="sick-blue" href="https://www.elastic.co/guide/en/elasticsearch/reference/6.3/query-dsl-query-string-query.html#_fuzziness">fuzzy</a>
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Proximity
            </th>
            <td className="blue-line"> <pre className="app-pre">
            "fox quick"~5
            </pre> </td>
            <td className="blue-line">
            More information about <a className="sick-blue" href="https://www.elastic.co/guide/en/elasticsearch/reference/6.3/query-dsl-query-string-query.html#_proximity_searches">proximity</a>
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Excluding Keyword
            </th>
            <td className="blue-line"> <pre className="app-pre">
            -Fred
            </pre> </td>
            <td className="blue-line">
            Term "Fred" should not be present
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Excluding Keyword
            </th>
            <td className="blue-line"> <pre className="app-pre">
            NOT (name:"Fred")
            </pre> </td>
            <td className="blue-line">
            Excludes name "Fred"
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Excluding Keyword
            </th>
            <td className="blue-line"> <pre className="app-pre">
            ! (name:"Fred")
            </pre> </td>
            <td className="blue-line">
            Excludes name "Fred"
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Field Exists and is Non-Null
            </th>
            <td className="blue-line"> <pre className="app-pre">
            _exists_:title
            </pre> </td>
            <td className="blue-line">
            Field "title" has any non-null value
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Field Does Not Exist
            </th>
            <td className="blue-line"> <pre className="app-pre">
            NOT _exists_:title
            </pre> </td>
            <td className="blue-line">
            Field "title" has a null value
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Field has Value
            </th>
            <td className="blue-line"> <pre className="app-pre">
            CodeValue:*
            </pre> </td>
            <td className="blue-line">
            Must be non-null in field "CodeValue"
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Field Name with Space
            </th>
            <td className="blue-line"> <pre className="app-pre">
            Scheduled\ Date:foo
            </pre> </td>
            <td className="blue-line">
            Allow search of field "Scheduled Date"
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Wildcard in Field Name
            </th>
            <td className="blue-line"> <pre className="app-pre">
            city\*:something
            </pre> </td>
            <td className="blue-line">
            Allow search of field beginning with "city"
            </td>
          </tr>
        </tbody>
      </Table>


            <p></p>
            <hr className="blue-line" />
            <p></p>
            <h3 style={{paddingTop:'15px'}}>
              Available Search Fields
            </h3>
            <p></p>
            Below is a subset of the available fields to search on. A full list can be found <a className="sick-blue" href="https://github.com/aim-sk/aim-platform/wiki/Available-Fields-to-Search-By" target="_blank">here</a>.
            <p></p>

      <Table bordered>
        <tbody className="background-line blue-right-line blue-left-line">
          <tr>
            <th className="background-line blue-right-line center">
            High Sensitivity<br></br>Not Available
            </th>
            <th className="background-line blue-right-line blue-left-line center">
            Medium Sensitivity<br></br>Available
            </th>
            <th className="background-line blue-left-line center" >
            Low Sensitivity<br></br>Available
            </th>
          </tr>
        </tbody>
        <tbody className="background-line">
          <tr>
            <td className="background-line center blue-right-line">
            PatientID
            </td>
            <td className="background-line center blue-right-line">
            PatientSex
            </td>
            <td className="background-line center">
            ImageID
            </td>
          </tr>
        </tbody>
        <tbody className="background-line center">
          <tr>
            <td className="background-line center blue-right-line">
            AccessionNumber
            </td>
            <td className="background-line center blue-right-line">
            InstitutionName
            </td>
            <td className="background-line center">
            Location
            </td>
          </tr>
        </tbody>
        <tbody className="background-line center">
          <tr>
            <td className="background-line center blue-right-line">
            StudyID
            </td>
            <td className="background-line center blue-right-line">
            PatientAgeInt
            </td>
            <td className="background-line center">
            ImageType
            </td>
          </tr>
        </tbody>
                <tbody className="background-line center">
          <tr>
            <td className="background-line center blue-right-line">
            PatientAddress
            </td>
            <td className="background-line center blue-right-line">
            PatientBirthDate
            </td>
            <td className="background-line center">
            AcquisitionNumber
            </td>
          </tr>
        </tbody>
        <tbody className="background-line center">
          <tr>
            <td className="background-line center blue-right-line">
            PatientName
            </td>
            <td className="background-line center blue-right-line">
            AcquisitionDate
            </td>
            <td className="background-line center">
            InstanceNumber
            </td>
          </tr>
        </tbody>
        <tbody className="background-line">
          <tr>
            <td className="background-line blue-right-line center">
            •<br></br>•<br></br>•<br></br><a className="sick-blue" href="https://github.com/aim-sk/aim-platform/wiki/Available-Fields-to-Search-By" target="_blank">More</a>
            </td>
            <td className="background-line blue-right-line center">
            •<br></br>•<br></br>•<br></br><a className="sick-blue" href="https://github.com/aim-sk/aim-platform/wiki/Available-Fields-to-Search-By" target="_blank">More</a>
            </td>
            <td className="background-line center">
            •<br></br>•<br></br>•<br></br><a className="sick-blue" href="https://github.com/aim-sk/aim-platform/wiki/Available-Fields-to-Search-By" target="_blank">More</a>
            </td>
          </tr>
        </tbody>
      </Table>



          <hr className="blue-line" />
          <p></p>
          <h3 style={{paddingTop:'15px'}}>
          How to Download Metadata
          </h3>
          <p></p>

            <h4>
              Prerequisite: Download Helper Tool
            </h4>
            <p>
            To download metadata about your current search please install the <tt>elasticdump</tt> download helper tool. Note this will not download DICOM images.
            </p>
            <p>
            Install <a className="sick-blue" href="https://stedolan.github.io/jq/download/" target="_blank"><tt>elasticdump</tt></a> helper tool using the node package manager:
            </p>

            <pre className="app-pre">
              npm install elasticdump -g
            </pre>
            <h4>
              Example 1: Download Metadata
            </h4>
            Download all metadata associated with the images in your current search results. Run this command and wait for all metadata to be downloaded to the file <tt>output.json</tt>:
            <pre className="app-pre">{`
elasticdump \\
  --input=https://elasticimages.ccm.sickkids.ca \\
  --output=output.json \\
  --headers='{"X-Requested-With": "224400"}' \\
  --searchBody='${this.props.lastQuery}'
              `}
              </pre>
            <h4>
              Example 2: Download File Paths
            </h4>
            Download the file path locations of all the images in your current search results. This also requires the <tt>jq</tt> tool, download jq <a className="sick-blue" href="https://stedolan.github.io/jq/download/" target="_blank">here</a>. Run this command and wait for all the file paths to be downloaded to the file <tt>output.txt</tt>:
            <pre className="app-pre">{`
elasticdump \\
  --input=https://elasticimages.ccm.sickkids.ca \\
  --output=$ \\
  --headers='{"X-Requested-With": "224400"}' \\
  --searchBody='${this.props.lastQuery}' \\
| jq ._source.dicom_filepath | tee output.txt
              `}
              </pre>

      <p></p>
      <hr className="blue-line" />
      <p></p>
      <h3 style={{paddingTop:'15px'}}>
      Search Performance Considerations
      </h3>
      <div> <tt className="sick-blue">•</tt> It is best to specify and search within known fields names to speed up results. Not specifying field names will searching across all fields which is much slower. </div>
      <div> <tt className="sick-blue">•</tt> Searches will timeout after 1 minute. If this happens to you then you will have to be more specific on which fields you search.</div>
      <div> <tt className="sick-blue">•</tt> Number of search terms is limited to 1024. That means maximum 1024 PatientIDs or AccessionNumbers can be searched at once.</div>
      <p></p>



          </ModalBody>
          <ModalFooter>


<Table borderless>
        <tbody className="background-line">
          <tr>
            <th className="background-line shift-left">
            <a className="sick-blue" href="mailto:daniel.snider@sickkids.ca?subject=Diagnostic Imaging Archive Support" target="_blank">Support </a> Provided by <a className="sick-blue" href="https://ccm.sickkids.ca/" target="_blank">The Centre for Computational Medicine</a>
            </th>
            <th className="background-line shift-right">
            <Button color="secondary" onClick={this.toggle}>OK</Button>
            </th>
          </tr>
        </tbody>
</Table>
          </ModalFooter>
        </Modal>
        </button>
    );
  }
}

export default ModalExample;
