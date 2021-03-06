import json
import os
from tests.utils import (client, BaseClass, create_project, sanitize_highlight_region,
                load_data_file, load_yaml_file, get_project_files,
                load_wikifier_file, load_item_file)
    

project_folder=None #we need to use a global for some reason... self.project_folder does not work.




class TestBasicWorkflow(BaseClass):
    files_dir=os.path.join(os.path.dirname(__file__), "files_for_tests", "aid")
    expected_results_path=os.path.join(files_dir, "results.json")

    def test_01_add_project(self, client):
        #POST /api/project
        global project_folder
        project_folder=create_project(client)
        assert project_folder is not None 
        
    def test_01b_change_project_name(self, client):
        url='/api/project?project_folder={project_folder}'.format(project_folder=project_folder)
        ptitle="Unit test"
        response=client.put(url,
                data=dict(
                ptitle=ptitle
            )) 
        data = response.data.decode("utf-8")
        data = json.loads(data)
        assert data['project']['title']==ptitle

    def test_02_get_project_files(self, client):
        data=get_project_files(client, project_folder)
        data.pop('project')
        assert data == {
            'name': 'Unit test',
            'tableData': None,
            'yamlData': None,
            'wikifierData': None
        }

    def test_03_add_data_file(self, client):   
        filename=os.path.join(self.files_dir, "dataset.xlsx")
        response=load_data_file(client, project_folder, filename)
        data = response.data.decode("utf-8")
        data = json.loads(data)
        self.results_dict['add_data_file']=data
        data.pop('project')
        data['tableData'].pop('filename', None)
        self.expected_results_dict['add_data_file']['tableData'].pop('filename', None)
        self.compare_jsons(data, 'add_data_file')

    def test_05_add_wikifier_file(self, client):
        filename=os.path.join(self.files_dir, "consolidated-wikifier.csv")
        response=load_wikifier_file(client, project_folder, filename)
        data = response.data.decode("utf-8")
        data = json.loads(data)
        data.pop('project')
        self.results_dict['add_wikifier_file']=data
        self.compare_jsons(data, 'add_wikifier_file')


    def test_06_add_items_file(self, client):
        filename=os.path.join(self.files_dir, "kgtk_item_defs.tsv")
        response=load_item_file(client, project_folder, filename)
        data = response.data.decode("utf-8")
        data = json.loads(data)
        data.pop('project')
        self.results_dict['add_items']=data
        self.compare_jsons(data, 'add_items')

    def test_08_add_yaml_file(self, client):
        filename=os.path.join(self.files_dir, "test.yaml")
        response=load_yaml_file(client, project_folder, filename)
        data = response.data.decode("utf-8")
        data = json.loads(data)
        data.pop('project')
        self.results_dict['add_yaml']=data

        #some of the results are sent back as unordered lists and need to be compared separately
        dict_1=data["yamlRegions"]
        dict_2=self.expected_results_dict["add_yaml"]["yamlRegions"]
        sanitize_highlight_region(dict_1, dict_2)

        self.compare_jsons(data, 'add_yaml')

    def test_09_get_cell(self, client):
        #GET '/api/data/{project_folder}/cell/<col>/<row>'
        url='/api/data/cell/{col}/{row}?project_folder={project_folder}'.format(project_folder=project_folder, col="G", row=4)
        response=client.get(url) 
        data = response.data.decode("utf-8")
        data = json.loads(data)
        self.results_dict['get_cell']=data
        self.compare_jsons(data, 'get_cell')

    def test_11_get_download(self, client):
        #GET '/api/project/{project_folder}/download/<filetype>'
        url='/api/project/download/{filetype}?project_folder={project_folder}'.format(project_folder=project_folder, filetype="tsv")
        response=client.get(url) 
        data = response.data.decode("utf-8")
        data = json.loads(data)
        data=data["data"]
        with open(os.path.join(self.files_dir, "download.tsv"), 'r') as f:
            expected=f.read()
        assert expected==data

    def test_12_change_sheet(self, client):
        #GET /api/data/{project_folder}/<sheet_name>
        url='/api/data/{sheet_name}?project_folder={project_folder}'.format(project_folder=project_folder,sheet_name="Sheet4")
        response=client.get(url) 
        data = response.data.decode("utf-8")
        data = json.loads(data)
        self.results_dict['change_sheet']=data
        data['tableData'].pop('filename', None)
        self.expected_results_dict['change_sheet']['tableData'].pop('filename', None)
        self.compare_jsons(data, 'change_sheet')

    def test_12_wikify_region(self, client):
        #POST '/api/wikifier_service/{project_folder}'
        url='/api/wikifier_service?project_folder={project_folder}'.format(project_folder=project_folder)
        response=client.post(url,
                data=dict(
                action="wikify_region",
                region="I3:I8",
                context="wikifier test",
                flag="0"
                )
            )

        data = response.data.decode("utf-8")
        data = json.loads(data)
        data.pop('project')
        self.results_dict['wikify_region']=data
        self.compare_jsons(data, 'wikify_region')

    def test_14_settings(self, client):
        from t2wml.settings import t2wml_settings
        #PUT '/api/project/{project_folder}/settings'
        url='/api/project/settings?project_folder={project_folder}'.format(project_folder=project_folder)
        endpoint='https://query.wikidata.org/bigdata/namespace/wdq/sparql'
        response=client.put(url,
                data=dict(
                endpoint=endpoint, 
                warnEmpty=False
            )) 
        assert t2wml_settings.wikidata_provider.sparql_endpoint==endpoint

        #GET '/api/project/{project_folder}/settings'
        url='/api/project/settings?project_folder={project_folder}'.format(project_folder=project_folder)
        response=client.get(url) 
        data = response.data.decode("utf-8")
        data = json.loads(data)
        assert data["endpoint"]=='https://query.wikidata.org/bigdata/namespace/wdq/sparql'
        assert data["warnEmpty"]==False
    
    def xtest_999_save(self):
        #used when overwriting all old results with new ones 
        with open(self.expected_results_path, 'w') as f:
            json.dump(self.results_dict, f, sort_keys=False, indent=4)



class TestLoadingProject(BaseClass):
    files_dir=os.path.join(os.path.dirname(__file__), "files_for_tests", "aid")
    expected_results_path=os.path.join(files_dir, "project_results.json")

    def test_10_load_from_path(self, client):
        url='/api/project/load?project_folder={path}'.format(path=self.files_dir)
        response=client.post(url)
        data = response.data.decode("utf-8")
        data = json.loads(data)
        assert response.status_code==201
    
    def test_11_get_loaded_yaml_files(self, client):
        url= '/api/project?project_folder={path}'.format(path=self.files_dir)
        response=client.get(url)
        data = response.data.decode("utf-8")
        data = json.loads(data)
        data.pop('project')
        self.results_dict['load_from_path']=data
        #some of the results are sent back as unordered lists and need to be compared separately
        set_keys=[]
        dict_1=data["yamlData"]["yamlRegions"]
        dict_2=self.expected_results_dict["load_from_path"]["yamlData"]["yamlRegions"]
        sanitize_highlight_region(dict_1, dict_2)

        data['tableData'].pop('filename', None)
        self.expected_results_dict['load_from_path']['tableData'].pop('filename', None)

        self.compare_jsons(data, 'load_from_path')

    