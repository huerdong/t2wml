import React, { Component } from 'react';
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
import { observer } from "mobx-react"
import wikiStore from '../data/store';


interface FilesState {
  project: any;
}

@observer
class Files extends Component<{}, FilesState> {
    constructor(props: {}) {
        super(props);

        this.state = {
            project: null
        };

        wikiStore.project.updateFiles = (project: any) => this.updateFiles(project);

    }

    updateFiles(project: any) {
        this.setState({project: project});
    }

    buildFilesTree() {
        const filesTree = [];
        if (this.state.project) {
            for (const fileType of Object.keys(this.state.project)) {
                if (Array.isArray(this.state.project[fileType])) {
                    const files = [];
                    for (const file of this.state.project[fileType]) {
                        files.push(<li key={file}>{file}</li>)
                    }
                    filesTree.push(
                    <li key={fileType}>{fileType}
                        <ul>{files}</ul>
                    </li>);
                }
            }
        }
        return filesTree;
    }

   

  render() {
    const filesTree = this.buildFilesTree();

    return (
      <div>
          Files
          <ul>
            { filesTree }
          </ul>
      </div>
    );
  }
}

export default Files;