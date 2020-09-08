import { observable } from 'mobx';
import { ipcRenderer } from 'electron';
import { DisplayMode } from '@/shared/types';

class ProjectState {
    @observable public pid: string;
    @observable public path?: string;
    @observable public updateFiles: (project: any) => void;

    constructor() {
        this.pid = '';
        this.path = undefined;
        this.updateFiles = () => undefined;
    }
}

type EditorsStatus = "Wikifier" | "YamlEditor";
class EditorsState {
    @observable public nowShowing: EditorsStatus = "Wikifier";
}

class TabletState {
    @observable public isCellSelectable: boolean;

    @observable public showSpinner: boolean;
    @observable public errorCells: string[] | undefined;
    @observable public updateYamlRegions: (newYamlRegions?: any) => void;
    @observable public updateQnodeCells: (qnodes?: any, rowData?: any) => void;
    @observable public updateTableData: (tableData: any) => void; // tableData as type TableData
    @observable public updateStyleByCell: (colName: string | number | null, rowName: string | number | null, style: any, override?: boolean) => void;
    @observable public handleOpenWikifierFile:(event: any) => void;
    
    constructor() {
        this.isCellSelectable = false;

        this.showSpinner = false;
        this.errorCells = undefined;
        this.updateYamlRegions = () => undefined;
        this.updateQnodeCells = () => undefined;
        this.updateTableData = () => undefined;
        this.updateStyleByCell = () => undefined;
        this.handleOpenWikifierFile = () => undefined;
    }
}

class SettingsState {
    @observable public sparqlEndpoint: string;
    @observable public warnEmpty: boolean;

    constructor() {
        this.sparqlEndpoint = '';
        this.warnEmpty = false;
    }
}

class WikifierInnerState {
    @observable public qnodeData: any = {};
    @observable public currRegion = ''; // Is it needed?
}
class WikifierState {
    @observable public showSpinner: boolean;
    @observable public updateWikifier: (qnodeData?: any, rowData?: any) => void;
    @observable public state: WikifierInnerState | undefined;
    @observable public scope: number; // Is it needed?

    constructor() {
        this.showSpinner = false;
        this.updateWikifier = () => undefined;
        this.state = new WikifierInnerState();
        this.scope = 0;
    }
}

class OutputState {
    @observable public showSpinner: boolean;
    @observable public isDownloadDisabled: boolean;
    @observable public removeOutput: () => void;
    @observable public updateOutput: (colName: string, rowName: string, json: any) => void;


    constructor() {
        this.showSpinner = false;
        this.isDownloadDisabled = true;
        this.removeOutput = () => undefined;
        this.updateOutput = () => undefined;
    }
}

class YamlEditorState {
    @observable public updateYamlText: (yamlText?: string | null) => void;

    constructor() {
        this.updateYamlText = () => undefined;
    }
}


class WikiStore {
    @observable public project = new ProjectState();
    @observable public editors = new EditorsState();
    @observable public table = new TabletState();
    @observable public settings = new SettingsState();
    @observable public wikifier = new WikifierState();
    @observable public output = new OutputState();
    @observable public yaml = new YamlEditorState();
    @observable public displayMode: DisplayMode = 'project-list';

    public changeProject(pid?: string, path?: string) {
        if (pid) {
            debugger;
            this.displayMode = 'project';
            this.project.pid = pid;
            if (path) {
                ipcRenderer.send('show-project', path)
            }
        } else {
            this.displayMode = 'project-list';
            ipcRenderer.send('show-project', null);
        }
    }
}


const wikiStore = new WikiStore();
export default wikiStore;
