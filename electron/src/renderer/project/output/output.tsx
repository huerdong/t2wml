import React, { Component } from 'react';

// App
import { Button, Card, Spinner } from 'react-bootstrap';

// Output
import Downloader from 'js-file-download';

// console.log
import { LOG, ErrorMessage } from '../../common/general';
import * as utils from '../../common/utils'
import RequestService from '../../common/service';
import ToastMessage from '../../common/toast';

import { observer } from "mobx-react";
import wikiStore from '../../data/store';
import Download from './download';
import ShowOutput from './show-output';

interface OutputState {
  showSpinner: boolean,
  currCol: string;
  currRow: string;
  // data
  valueCol: string | null;
  valueRow: string | null;
  value: string | null;
  unitName: string | null;
  unitID: string | null;
  itemID: string | null;
  itemName: string | null;
  itemCol: string | undefined;
  itemRow: string | undefined;
  propertyID: string | null;
  qualifiers: any; //  null;
  cache: any; // cache for Wikidata queries
  errors: string;

  // download
  showDownload: boolean,
  isDownloadDisabled: boolean,
  isDownloading: boolean;

  propertyName: string;
  errorMessage: ErrorMessage;

  queryDataCount: number;
}

@observer
class Output extends Component<{}, OutputState> {
  private requestService: RequestService;
  private pid: string;
  
  constructor(props: {}) {
    super(props);
    this.requestService = new RequestService();
    this.pid = wikiStore.project.pid;

    // init state
    this.state = {

      // appearance
      showSpinner: wikiStore.output.showSpinner,

      // data
      valueCol: null,
      valueRow: null,
      value: null,
      unitName: null,
      unitID: null,
      itemID: null,
      itemName: null,
      itemCol: undefined,
      itemRow: undefined,
      propertyID: null,
      qualifiers: null,
      cache: {}, // cache for Wikidata queries,
      errors: '',

      // download
      showDownload: false,
      isDownloadDisabled: wikiStore.output.isDownloadDisabled,
      isDownloading: false,

      errorMessage: {} as ErrorMessage,
      queryDataCount: 0,
    } as OutputState;


    wikiStore.output.removeOutput = () => this.removeOutput();
    wikiStore.output.updateOutput = (colName: string, rowName: string, json: any) => this.updateOutput(colName, rowName, json);
  }

  handleDoDownload(fileName: string, fileType: string) {
    this.setState({ errorMessage: {} as ErrorMessage });  
    const filename = fileName + "." + fileType;

    // before sending request
    this.setState({ isDownloading: true, showDownload: false });
    // send request
    console.log("<Output> -> %c/download%c for file: %c" + filename, LOG.link, LOG.default, LOG.highlight);
    this.requestService.downloadResults(this.pid, fileType).then((json) => {
      console.log("<Output> <- %c/download%c with:", LOG.link, LOG.default);
      console.log(json);

      // do something here
      const { error } = json;

      // if failure
      if (error) {
        throw Error(error);
      }

      // else, success
      const { data, internalErrors} = json;
      if (internalErrors !== undefined){
          console.log("ERRORS in input to download:")
          console.log(internalErrors);
          this.setState({errorMessage:     
            {errorCode: 400,
            errorTitle: "Problems within statements",
            errorDescription: "Although the file downloaded, there were errors in the input, check console for details"} as ErrorMessage
        })
      }
      Downloader(data, filename);

      // follow-ups (success)
      this.setState({ isDownloading: false });

    }).catch((error: ErrorMessage) => {
    //   console.log(error);
      error.errorDescription += "\n\nCannot download!";
      this.setState({ errorMessage: error });

      // follow-ups (failure)
      this.setState({ isDownloading: false });
    });
  }

  cancelDownload() {
      this.setState({showDownload: false});
  }

  removeBorders() {
    // remove value border
    let col: string | undefined = this.state.currCol;
    let row: string | undefined = this.state.currRow;
    if (col !== undefined && row !== undefined) {
        wikiStore.table.updateStyleByCell(col, row, { "border": "" });
    }

    // remove item border
    col = this.state.itemCol;
    row = this.state.itemRow;
    if (col !== undefined && row !== undefined) {
      wikiStore.table.updateStyleByCell(col, row, { "border": "" });
    }

    // remove qualifier borders
    const qualifiers = this.state.qualifiers;
    if (qualifiers !== undefined && qualifiers != null) {
      for (let i = 0, len = qualifiers.length; i < len; i++) {
        col = qualifiers[i]["col"];
        row = qualifiers[i]["row"];
        if (col && row) {
            wikiStore.table.updateStyleByCell(col, row, { "border": "" });
        }
      }
    }
  }

  updateOutput(colName: string, rowName: string, json: any) {
    // remove current status
    this.removeOutput();
    if(json["error"]) {
        this.setState({errors: JSON.stringify(json["error"])});
    }
    
    this.setState({
      valueCol: colName,
      valueRow: rowName
    });

    if (json["statement"] === undefined) return;
    const qnodesLabel = json["qnodesLabels"];

    // item
    const itemID = json["statement"]["item"];
    // const itemName = window.TableViewer.state.rowData[row][col];
    this.setState({ itemID: itemID, itemName: qnodesLabel[itemID] });
    
    if (json["statement"]["cell"]) {
      const [col, row] = json["statement"]["cell"].match(/[a-z]+|[^a-z]+/gi);
      wikiStore.table.updateStyleByCell(col, row, { "border": "1px solid black !important" });
      this.setState({ itemCol: col, itemRow: row });
    }
    // property
    const propertyID = json["statement"]["property"];
    this.setState({ propertyID: propertyID, propertyName: qnodesLabel[propertyID] });

    // value
    const value = json["statement"]["value"];
    this.setState({ value: value });
    wikiStore.table.updateStyleByCell(colName, rowName, { "border": "1px solid hsl(150, 50%, 40%) !important" });
    this.setState({ currCol: colName, currRow: rowName });

    // unit
    if (json["statement"]["unit"]) {
      let unitName = json["statement"]["unit"];
      let unitID = null;
      if (/^[PQ]\d+$/.test(unitName)) {
        unitID = unitName;
        unitName = qnodesLabel[unitName];
      }
      this.setState({ unitName: unitName, unitID: unitID });
    } else {
      this.setState({ unitName: null });
    }

    // qualifiers
    const temp = json["statement"]["qualifier"];
    const qualifiers = [];
    if (temp !== undefined) {
      for (let i = 0, len = temp.length; i < len; i++) {
        const qualifier: any = {};

        qualifier["propertyID"] = temp[i]["property"];
        qualifier["propertyName"] = qnodesLabel[qualifier["propertyID"]];

        qualifier["valueName"] = temp[i]["value"];
        if (/^[PQ]\d+$/.test(qualifier["valueName"])) {
          qualifier["valueID"] = qualifier["valueName"];
          qualifier["valueName"] = qnodesLabel[qualifier["valueName"]];
        }

        if (temp[i]["cell"] !== undefined && temp[i]["cell"] !==null) {
          const [q_col, q_row] = temp[i]["cell"].match(/[a-z]+|[^a-z]+/gi);
          qualifier["col"] = q_col;
          qualifier["row"] = q_row;
          // let hue = utils.getHueByRandom(10); // first param is the total number of colors
          const hue = utils.getHueByQnode(10, qualifier["propertyID"]);
          wikiStore.table.updateStyleByCell(q_col, q_row, { "border": "1px solid hsl(" + hue + ", 100%, 40%) !important" });
        }

        qualifiers.push(qualifier);
      }

    }
    this.setState({ qualifiers: qualifiers });
  }
  
  removeOutput() {
    this.removeBorders();
    this.setState({
      valueCol: null,
      valueRow: null,
      value: null,
      unitName: null,
      unitID: null,
      itemID: null,
      itemName: null,
      itemCol: undefined,
      itemRow: undefined,
      propertyID: null,
      qualifiers: null,
      errors: '',
    });
  }

  render() {
    return (
      <div className="w-100 h-100 p-1">
        <Download showDownload={this.state.showDownload}
            handleDoDownload={(fileName: string, fileType: string) => this.handleDoDownload(fileName, fileType)}
            cancelDownload={() => this.cancelDownload()} />
        {this.state.errorMessage.errorDescription ? <ToastMessage message={this.state.errorMessage}/> : null }

        <Card className="w-100 h-100 shadow-sm">

          {/* card header */}
          <Card.Header style={{ height: "40px", padding: "0.5rem 1rem", background: "#990000" }}>

            {/* title */}
            <div
              className="text-white font-weight-bold d-inline-block text-truncate"
              style={{ width: "calc(100% - 90px)", cursor: "default" }}
            >Output</div>

            {/* button to download */}
            <Button
              className="d-inline-block float-right"
              variant="outline-light"
              size="sm"
              style={{ padding: "0rem 0.5rem", width: "83px" }}
              onClick={() => this.setState({ showDownload: true })}
              disabled={wikiStore.output.isDownloadDisabled || this.state.isDownloading}
            >
              {this.state.isDownloading ? <Spinner as="span" animation="border" size="sm" /> : "Download"}
            </Button>
          </Card.Header>

          {/* card body */}
          <Card.Body className="w-100 h-100 p-0" style={{ overflow: "auto" }}>

            {/* loading spinner */}
            <div className="mySpinner" hidden={!wikiStore.output.showSpinner}>
              <Spinner animation="border" />
            </div>

            {/* output */}
            { this.state.queryDataCount === 0 ? 
            <div className="w-100 p-3" style={{ height: "1px" }}>
            <ShowOutput
                errors={this.state.errors}
                itemName={this.state.itemName}
                itemID={this.state.itemID}
                propertyID={this.state.propertyID}
                propertyName={this.state.propertyName}
                value={this.state.value}
                unitName={this.state.unitName}
                unitID={this.state.unitID}
                qualifiers={this.state.qualifiers}
            />
            </div> : null }
          </Card.Body>
        </Card>
      </div>
    );
  }
}

export default Output;
