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
        {/*Setting up header with Help icon and X on top-right corner*/}
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
          {/*All of the examples of queries that can be performed are listed*/}
          <h3>
            Search Examples
          </h3>
          <p></p>
        {/*Link to ElasticSearch's query string query syntax page*/}
            This archive's search box allows queries to be entered that follow the "String Query" syntax, which is a mini-language in ElasticSearch. Below we summarize possible searches that can be performed. For more info visit the <a className="sick-blue" href="https://www.elastic.co/guide/en/ElasticSearch/reference/current/query-dsl-query-string-query.html#query-string-syntax" target="_blank">ElasticSearch docs</a>.
            <p></p>

      {/*The table in which all the queries are listed and explained.
         Each body of the table contains the title of the search, an example
          of the seach, and the explanation of the search*/}
      <Table>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            All Fields (slow)
            </th>
            <td className="blue-line"> <pre className="app-pre">
            brain
            </pre> </td>
            <td className="blue-line">
            Case-insensitive search across entire database
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Exact Field (fastest)
            </th>
            <td className="blue-line"> <pre className="app-pre">
            BodyPartExamined:brain
            </pre> </td>
            <td className="blue-line">
            Case-insensitive search in one field. Field name is case-sensitive
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Multiple Fields (fast)
            </th>
            <td className="blue-line"> <pre className="app-pre">
            fields:[a,b,c] brain
            </pre> </td>
            <td className="blue-line">
            "a", "b" and "c" will be the only fields searched
            </td>
          </tr>
          </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Boolean
            </th>
            <td className="blue-line"> <pre className="app-pre">
            (brain OR head) AND NOT chest
            </pre> </td>
            <td className="blue-line">
            Logical oprators can be grouped by parent­heses
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Many PatientIDs
            </th>
            <td className="blue-line"> <pre className="app-pre">
            fields:PatientID ID1 ID2 ...
            </pre> </td>
            <td className="blue-line">
            Fast PatientID searching. Max 1024 IDs at a time
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Accession Numbers
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
            PatientAge:&#60;8
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
          {/*Link to webpage that gives descriptions and examples of regex*/}
            More information about <a className="sick-blue" href="https://www.elastic.co/guide/en/ElasticSearch/reference/current/query-dsl-regexp-query.html#regexp-syntax">regex</a> searches
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Wildcard
            </th>
            <td className="blue-line"> <pre className="app-pre">
            che?t scan*
            </pre> </td>
            <td className="blue-line">
            "­?" to replace a single character, and "­*" to replace zero or more characters
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Fuzzy
            </th>
            <td className="blue-line"> <pre className="app-pre">
            haert~
            </pre> </td>
            <td className="blue-line">
          {/*Link to ElasticSearch page about fuzzy searches*/}
            More information about <a className="sick-blue" href="https://www.elastic.co/guide/en/ElasticSearch/reference/6.3/query-dsl-query-string-query.html#_fuzziness">fuzzy</a> searches
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Proximity
            </th>
            <td className="blue-line"> <pre className="app-pre">
            "cancer of bone"~5
            </pre> </td>
            <td className="blue-line">
          {/*Link to ElasticSearch page about proximity searches*/}
            More information about <a className="sick-blue" href="https://www.elastic.co/guide/en/ElasticSearch/reference/6.3/query-dsl-query-string-query.html#_proximity_searches">proximity</a> searches
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Field has Value
            </th>
            <td className="blue-line"> <pre className="app-pre">
            StudyComments:/.*/
            </pre> </td>
            <td className="blue-line">
            Field must exist and contain 1 or more characters
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Field Missing Value
            </th>
            <td className="blue-line"> <pre className="app-pre">
            StudyComments.keyword:""
            </pre> </td>
            <td className="blue-line">
            Field must exist but is empty
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Field Does Not Exist
            </th>
            <td className="blue-line"> <pre className="app-pre">
            NOT _exists_:StudyComments
            </pre> </td>
            <td className="blue-line">
            Field not present in image
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Field Exists
            </th>
            <td className="blue-line"> <pre className="app-pre">
            _exists_:StudyComments
            </pre> </td>
            <td className="blue-line">
            Field exists but could be empty
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
            he\*:something
            </pre> </td>
            <td className="blue-line">
            Allow search of field beginning with "he"- heart and head would both satisfy
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Patient Age
            </th>
            <td className="blue-line"> <pre className="app-pre">
            PatientAge:>9
            </pre> </td>
            <td className="blue-line">
            Patients older than 9 years of age are searched
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Date
            </th>
            <td className="blue-line"> <pre className="app-pre">
            AcquisitionDate:>2011/11/16
            </pre> </td>
            <td className="blue-line">
            Any acquisition dates after 2011/11/16 are searched
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Time
            </th>
            <td className="blue-line"> <pre className="app-pre">
            Time:&lt;12:00:00
            </pre> </td>
            <td className="blue-line">
            Any times before 12:00:00 are searched
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Exact
            </th>
            <td className="blue-line"> <pre className="app-pre">
            ReasonForStudy.keyword:"High fever"
            </pre> </td>
            <td className="blue-line">
            The exact Accession Number is the only result given
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Inclusive Ranges
            </th>
            <td className="blue-line"> <pre className="app-pre">
            Date:[2010-01-01 TO 2010-12-31]
            </pre> </td>
            <td className="blue-line">
            [] are used for inclusive ranges
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Exclusive Ranges
            </th>
            <td className="blue-line"> <pre className="app-pre">
            Date:&#123;2010-01-01 TO 2010-12-31}
            </pre> </td>
            <td className="blue-line">
            &#123;} are used for exclusive ranges
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Combination Ranges
            </th>
            <td className="blue-line"> <pre className="app-pre">
            Date:&#123;2010-01-01 TO 2010-12-31]
            </pre> </td>
            <td className="blue-line">
            [] and &#123;} can be used together to specify one end point as included and the other as not included, respectively
            </td>
          </tr>
        </tbody>
        <tbody className="blue-line">
          <tr>
            <th className="blue-line">
            Boosting Relevance
            </th>
            <td className="blue-line"> <pre className="app-pre">
            Left arm^2
            </pre> </td>
            <td className="blue-line">
            Arm is specified as more relevant than left in the search
            </td>
          </tr>
        </tbody>
      </Table>

      {/*A list of the fields that can be searched and those that can't be
         There are three parts to the list; searches that can't be performed
          due to increased sensitivity, and searches that can be performed
          that have medium and low sensitivity*/}
            <p></p>
            <hr className="blue-line" />
            <p></p>
            <h3 style={{paddingTop:'15px'}}>
              Available Search Fields
            </h3>
            <p></p>
            {/*Link to wiki page that shows all possible searches*/}
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
            Allergies
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
            {/*Link to wiki page that shows all possible searches*/}
            <td className="background-line blue-right-line center">
            •<br></br>•<br></br>•<br></br><a className="sick-blue" href="https://github.com/aim-sk/aim-platform/wiki/Available-Fields-to-Search-By" target="_blank">More</a>
            </td>
            {/*Link to wiki page that shows all possible searches*/}
            <td className="background-line blue-right-line center">
            •<br></br>•<br></br>•<br></br><a className="sick-blue" href="https://github.com/aim-sk/aim-platform/wiki/Available-Fields-to-Search-By" target="_blank">More</a>
            </td>
            {/*Link to wiki page that shows all possible searches*/}
            <td className="background-line center">
            •<br></br>•<br></br>•<br></br><a className="sick-blue" href="https://github.com/aim-sk/aim-platform/wiki/Available-Fields-to-Search-By" target="_blank">More</a>
            </td>
          </tr>
        </tbody>
      </Table>



      <p style={{paddingTop:'5px'}}></p>
      <hr className="blue-line" />
      <p></p>

      <h3 style={{paddingTop:'15px'}}>
        How to Find Radiology Text Reports
      </h3>


    <p></p>
      <h4>Method 1: Find report in the dicom metadata</h4>
      <p></p>

    <div className="sml-padding-bottom"> <tt className="sick-blue">•</tt> Click on the image that you are interested in. </div>
    <div className="sml-padding-bottom"> <tt className="sick-blue">•</tt> On the next webpage, select the tag button in the top left-hand corner of the screen:
    <img className="grid" src="/static/tabs_image.png" alt="tabs"/>
    </div>
    <div className="sml-padding-bottom"> <tt className="sick-blue">•</tt> Scroll through the metadata on the following webpage and look at the Values column. Any values that begin with "Report" is from the radiology report for this image. </div>

      <p></p>
      <h4>Method 2: Find report using ElasticSearch API</h4>
      <p></p>

      Here is an basic example cURL used to get the first 10 reports:

      <pre className="app-pre"> {`
curl -v -H 'Content-Type: application/json' \\
        -H 'X-Requested-With:224400' \\
-XPOST 'https://elasticimages.ccm.sickkids.ca/report/report/_search' -d ' 
{
  "query" : {
      "match_all" : {}
  }
}'`}
          </pre> 
          <div className="sml-padding-bottom"> <tt className="sick-blue">•</tt> <code>cURL</code> is a command line tool used to make HTTP requests.</div>
          <div className="sml-padding-bottom"> <tt className="sick-blue">•</tt> <code>elasticimages.ccm.sickkids.ca</code> is location of the ElasticSearch API.</div>
          <div className="sml-padding-bottom"> <tt className="sick-blue">•</tt> Place your password in the header <code>X-Requested-With:</code> section.</div>
          <div className="sml-padding-bottom"> <tt className="sick-blue">•</tt> The query <code>match_all</code> will return all results. By default only 10 are displayed at once.</div>



      <p style={{paddingTop:'5px'}}></p>
      <hr className="blue-line" />
      <p></p>

      <h3 style={{paddingTop:'15px'}}>
        How to directly query ElasticSearch API
      </h3>

      Here is an basic example cURL used to get the metadata about the first 10 images in ElasticSearch:

      <pre className="app-pre"> {`
curl -v -H 'Content-Type: application/json' \\
        -H 'X-Requested-With:224400' \\
-XPOST 'https://elasticimages.ccm.sickkids.ca/image/image/_search' -d ' 
{
  "query" : {
      "match_all" : {}
  }
}'`}
          </pre> 
          <div className="sml-padding-bottom"> <tt className="sick-blue">•</tt> <code>cURL</code> is a command line tool used to make HTTP requests.</div>
          <div className="sml-padding-bottom"> <tt className="sick-blue">•</tt> <code>elasticimages.ccm.sickkids.ca</code> is location of the ElasticSearch API.</div>
          <div className="sml-padding-bottom"> <tt className="sick-blue">•</tt> Place your password in the header <code>X-Requested-With:</code> section.</div>
          <div className="sml-padding-bottom"> <tt className="sick-blue">•</tt> The query <code>match_all</code> will return all results. By default only 10 are displayed at once. For more than 10 see the next section called "How to Download Metadata".</div>


        {/*Explanation of how to be able to download metadata*/}
        <p style={{paddingTop:'5px'}}></p>
          <hr className="blue-line" />
          <p></p>
          <h3 style={{paddingTop:'15px'}}>
          How to Download Metadata
          </h3>
          <p></p>

        {/*Explanation of the prerequisties needed to download the metadata*/}
            <h4>
              Prerequisite: Download Helper Tool
            </h4>
            <p>
            To download metadata about your current search please install the <code>elasticdump</code> download helper tool. Note this will not download DICOM images but it will download DICOM header information, aka. metadata.
            </p>
            <p>
          {/*Link to webpage about downloading jq*/}
            Install <a className="sick-blue" href="https://stedolan.github.io/jq/download/" target="_blank"><code>elasticdump</code></a> helper tool using the node package manager:
            </p>
            <pre className="app-pre">
              npm install elasticdump -g
            </pre>

        {/*Explanation of the first possible way to download metadata*/}
            <h4>
              Example 1: Download Metadata
            </h4>
            Download all metadata associated with the images in your current search results. Run this command and wait for all metadata to be downloaded to the file <code>output.json</code>:
        {/*Command to download metadata to otuput.json*/}
            <pre className="app-pre">{`
elasticdump \\
  --input=https://elasticimages.ccm.sickkids.ca \\
  --output=output.json \\
  --headers='{"X-Requested-With": "224400"}' \\
  --searchBody='${this.props.lastQuery}'
              `}
              </pre>

          {/*Explanation of the second possible way to download metadata*/}
            <h4>
              Example 2: Download File Paths
            </h4>
            Download the file path locations of all the images in your current search results. This also requires the <code>jq</code> tool, download jq <a className="sick-blue" href="https://stedolan.github.io/jq/download/" target="_blank">here</a>. Run this command and wait for all the file paths to be downloaded to the file <code>output.txt</code>:
        {/*Command to download file paths to otuput.txt*/}
            <pre className="app-pre">{`
elasticdump \\
  --input=https://elasticimages.ccm.sickkids.ca \\
  --output=$ \\
  --headers='{"X-Requested-With": "224400"}' \\
  --searchBody='${this.props.lastQuery}' \\
| jq ._source.dicom_filepath | tee output.txt
              `}
              </pre>


    <p style={{paddingTop:'5px'}}></p>
    <hr className="blue-line" />
    <p></p>
    <h3 style={{paddingTop:'15px'}}>
        How De-identification Works
    </h3>
     <p></p>
      De-identification is performed on all PHI with the found PHI replaced and associated with a specific UUID. PHI that has identical values will be associated with the same UUID. For example, September 9, 1999 and 09/09/1999 will have the same UUID as they are the same date in different forms. There are two forms in which PHI can be identified; identical matches or fuzzy matches. Identical PHI matches are quickly replaced with their UUID counterpart. For fuzzy matches, dates within 2 digits differences will be matched and replaced, and for text if 50% of characters match a PHI term it will be replaced. UUID to PHI re-identification can be performed for a fee and with REB approval.
      <p></p>


    <p style={{paddingTop:'5px'}}></p>
    <hr className="blue-line" />
    <p></p>
    <h3 style={{paddingTop:'15px'}}>
      How to View 3D Images
    </h3>
    Many of our images are stored as 2D images but can be combined and viewed as a 3D z-stack using 3D slicer. 3D slicer is a software application that can be downloaded for analysis and visualization of medical images, such as examining 3D images and scanning through the layers of the image. The software can take a folder of dicoms and display a 3D stack of all the dicoms in a combined view. Note this tool is not developed or supported by the Centre for Computational Medicine.
    <p></p>
    <img src="/static/3D-slicer.png" alt="3D Slicer"/>

      <p style={{paddingTop:'15px'}}></p>
      <hr className="blue-line" />
      <p></p>
    <p></p>
    {/*List of of things that should be taken into considering when performing a search*/}
      <h3 style={{paddingTop:'15px'}}>
      Search Tips
      </h3>
      <div className="sml-padding-bottom"> <tt className="sick-blue">•</tt> It is best to specify and search within known fields names to speed up results. Not specifying field names will searching across all fields which is much slower. </div>
      <div className="sml-padding-bottom"> <tt className="sick-blue">•</tt> Searches will timeout after 1 minute. If this happens to you then you will have to be more specific on which fields you search.</div>
      <div className="sml-padding-bottom"> <tt className="sick-blue">•</tt> Number of search terms is limited to 1024. That means maximum 1024 PatientIDs or AccessionNumbers can be searched at once.</div>
      <div className="sml-padding-bottom"><tt className="sick-blue">•</tt> The parameter <a className="sick-blue" href="https://www.elastic.co/guide/en/elasticsearch/reference/2.4/query-dsl-minimum-should-match.html#query-dsl-minimum-should-match" target="_blank">minimum_should_match </a> can be used to specify the amount of exact matches there are between the query performed and the results given.</div>



  </ModalBody>


    {/*Link for where a user can access support or who they can email for support*/}
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
