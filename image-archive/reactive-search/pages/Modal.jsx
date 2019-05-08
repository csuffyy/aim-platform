/* eslint react/no-multi-comp: 0, react/prop-types: 0 */

import React from 'react';
import { Button, Modal, ModalHeader, ModalBody, ModalFooter } from 'reactstrap';

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
                <i className="fa fa-download" /> Download{" "}
              </b>
            </div>

          </ModalHeader>
          <ModalBody>
            <h3>
              Prerequisite: Download Helper Tool
            </h3>
            <p>
            To download your current search please install the <tt>elasticdump</tt> download helper tool.
            </p>
            <p>
            Install <tt>elasticdump</tt> using the node package manager:
            </p>

            <pre className="app-pre">
              npm install elasticdump -g
            </pre>
            <h3>
              Option 1: Download Metadata
            </h3>
            Download all metadata associated with the images in your current search results. Run this command and wait for all metadata to be downloaded to the file <tt>output.json</tt>:
            <pre className="app-pre">{`
elasticdump \\
  --input=https://elasticimages.ccm.sickkids.ca \\
  --output=output.json \\
  --headers='{"X-Requested-With": "224400"}' \\
  --searchBody='${this.props.lastQuery}'
              `}
              </pre>
            <h3>
              Option 2: Download File Paths
            </h3>
            Download the file path locations of all the images in your current search results. This also requires the <tt>jq</tt> tool, download jq <a href="https://stedolan.github.io/jq/download/" target="_blank">here</a>. Run this command and wait for all the file paths to be downloaded to the file <tt>output.txt</tt>:
            <pre className="app-pre">{`
elasticdump \\
  --input=https://elasticimages.ccm.sickkids.ca \\
  --output=$ \\
  --headers='{"X-Requested-With": "224400"}' \\
  --searchBody='${this.props.lastQuery}' \\
| jq ._source.dicom_filepath | tee output.txt
              `}
              </pre>
            <h3>
              Option 3: Download DICOMs
            </h3>
            A special request must be made to <a className="login-footer-link" href="mailto:daniel.snider@sickkids.ca?subject=Diagnostic Imaging Archive Download Request" target="_blank">Support</a>. Are you sure you want to download potentially millions of DICOMs? Typically users leave the DICOMs in place on the High Performance Computing Facility (HPF) and analyze them there without the need to download them to a desktop computer.
          </ModalBody>
          <ModalFooter>
            <Button color="secondary" onClick={this.toggle}>OK</Button>
          </ModalFooter>
        </Modal>
        </button>
    );
  }
}

export default ModalExample;
