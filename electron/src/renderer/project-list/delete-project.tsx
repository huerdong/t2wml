import React, {Component} from 'react';
import { Button, Col, Form, Modal, Row } from 'react-bootstrap';

interface DeleteProperties {
  // pid: number; Is it needed?
  showDeleteProject: boolean;

  handleDeleteProject: () => void;
  cancelDeleteProject: () => void;
}


class DeleteProject extends Component<DeleteProperties, {}> {

  render() {
    return (
      <Modal show={this.props.showDeleteProject} onHide={() => { /* do nothing */ }}>

        {/* header */}
        <Modal.Header style={{ background: "whitesmoke" }}>
          <Modal.Title>Delete&nbsp;Project</Modal.Title>
        </Modal.Header>

        {/* body */}
        <Modal.Body>
          <Form className="container">
            <Form.Group as={Row} style={{ marginTop: "1rem" }}>
              <Col sm="12" md="12">
                WARNING: This will remove the entire project directory, including all files and sub-directories.
                Are you sure you wish to proceed?
                
              </Col>
            </Form.Group>
          </Form>
        </Modal.Body>

        {/* footer */}
        <Modal.Footer style={{ background: "whitesmoke" }}>
        <Button variant="outline-dark" onClick={() => this.props.cancelDeleteProject()}>
            Cancel
          </Button>
          <Button variant="danger" onClick={() => this.props.handleDeleteProject()} style={{ backgroundColor: "#990000", borderColor: "#990000" }}>
            Confirm
          </Button>
        </Modal.Footer>
      </Modal>
    );
  }
}

export default DeleteProject;