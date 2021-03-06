import React, { Component } from 'react';

// icons
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faQuestion } from '@fortawesome/free-solid-svg-icons'

// App
import { Button, OverlayTrigger, Popover } from 'react-bootstrap';

import { observer } from "mobx-react";

interface LegendProperties {
    isCSV: boolean;
}

@observer
class TableLegend extends Component<LegendProperties, {}> {

  renderLegend() {
    return (
      <Popover className="shadow" style={{ backgroundColor: "rgba(255,255,255,0.8)" }} id="table">
        <div style={{ margin: "10px 30px" }}>
          <span><strong>Legend</strong>:&nbsp;</span>
          <span className="legend" style={{ backgroundColor: "white", color: "hsl(200, 100%, 30%)", marginLeft: "0" }}>wikified</span>
          <span className="legend" style={{ backgroundColor: "hsl(200, 50%, 90%)" }}>item</span>
          <span className="legend" style={{ backgroundColor: "hsl(250, 50%, 90%)" }}>qualifier</span>
          <span className="legend" style={{ backgroundColor: "hsl(150, 50%, 90%)" }}>data</span>
          <span className="legend" style={{ backgroundColor: "hsl(0, 0%, 90%)" }}>data&nbsp;(skipped)</span>
        </div>
      </Popover>
    );
  }

  render() {
      return (
          <OverlayTrigger overlay={this.renderLegend()} trigger={["hover", "focus"]} placement="left">
          <Button
            className="myPopover shadow"
            variant="secondary"
            style={this.props.isCSV ? { cursor: "default" } : { cursor: "default", bottom: "70px" }}
          >
            <FontAwesomeIcon icon={faQuestion} />
          </Button>
        </OverlayTrigger>
      );
  }
}

export default TableLegend;
