import json
import os
import sys
from pathlib import Path
from flask import request

from t2wml.utils.t2wml_exceptions import T2WMLException
from t2wml.api import Project as apiProject

import web_exceptions
from app_config import app
from models import (DataFile, ItemsFile, Project,
                    PropertiesFile, WikifierFile, YamlFile)

from t2wml_web import (download, get_cell, handle_yaml, serialize_item_table,
                       highlight_region, update_t2wml_settings, wikify)
from utils import (file_upload_validator, get_project_details, get_qnode_label,
                   make_frontend_err_dict, string_is_valid, upload_item_defs, table_data)
from web_exceptions import WebException
from t2wml_annotation_integration import AnnotationIntegration
from calc_params import CalcParams

debug_mode = False


def json_response(func):
    def wrapper(*args, **kwargs):
        try:
            data, return_code = func(*args, **kwargs)
            return json.dumps(data, indent=3), return_code
        except WebException as e:
            data = {"error": e.error_dict}
            return json.dumps(data, indent=3), e.code
        except T2WMLException as e:
            print(e.detail_message)
            data = {"error": e.error_dict}  # error code from the exception
            return json.dumps(data, indent=3), e.code
        except Exception as e:
            print(str(e))
            data = {"error": make_frontend_err_dict(e)}
            return json.dumps(data, indent=3), 500

    wrapper.__name__ = func.__name__  # This is required to avoid issues with flask
    return wrapper


##########NEW CODE:


#ALL THE POSTS/PUTS of files/projects (and one weird get)

@app.route('/api/project', methods=['POST'])
@json_response
def create_project():
    """
    This route creates an empty project file in a folder that has no project already
    :return:
    """
    project_path = request.form['project_path']
    #check we're not overwriting existing project
    project_file = Path(project_path) / ".t2wmlproj"
    if project_file.is_file():
        raise web_exceptions.ProjectAlreadyExistsException(project_path)
    #create project
    project=apiProject(project_path)
    project.title=Path(project_path).stem
    project.save()
    #return project json
    response = dict(project=project.__dict__)
    return response, 201


@app.route('/api/project', methods=['GET'])
@json_response
def load_project():
    """
    This route loads an existing project
    :return:
    """
    project_path=request.args['project_path']
    project=apiProject.load(project_path)
    response = dict(project=project.__dict__)
    return response, 201

@app.route('/api/data', methods=['PUT'])
@json_response
def put_data():
    """
    This route adds a data file to the project
    :return:
    """
    project_path=request.args['project_path']
    project=apiProject.load(project_path)
    data_path=request.args['data_path']
    project.add_data_file(data_path)
    project.save()
    response=dict(project=project.__dict__)
    calc_params=CalcParams(project_path, data_path, None)
    calc_params.sheet_name=calc_params.sheet_names[0]
    response["tableData"]=table_data(calc_params)
    return response, 201

@app.route('/api/wikifier', methods=['PUT'])
@json_response
def put_wikifier():
    """
    This route adds a wikifier file to the project
    :return:
    """
    project_path=request.args['project_path']
    project=apiProject.load(project_path)
    wikifier_path=request.args['wikifier_path']
    project.add_wikifier_file(wikifier_path)
    project.save()
    response=dict(project=project.__dict__)
    #response["wikifierData"]=None #TODO
    return response, 201

@app.route('/api/wikidata', methods=['PUT'])
@json_response
def put_wikidata():
    """
    This route adds wikidata definitions to the project
    :return:
    """
    project_path=request.args['project_path']
    project=apiProject.load(project_path)
    wikidata_path=request.args['wikidata_path']
    project.add_wikidata_file(wikidata_path) #TODO: needs to be implemented
    project.save()
    #TODO add to database
    #TODO return what was added/updated/failed
    return {}, 201

@app.route('/api/yaml', methods=['PUT'])
@json_response
def put_yaml():
    """
    This route adds a yaml file to the project
    :return:
    """
    project_path=request.args['project_path']
    project=apiProject.load(project_path)
    yaml_path=request.args['yaml_path']
    project.add_yaml_file(yaml_path)
    data_path=request.args.get('data_path')
    sheet_name=request.args.get('sheet_name')
    if data_path:
        project.associate_yaml_with_sheet(yaml_path, data_path, sheet_name)
    project.save()
    response=dict(project=project.__dict__)
    with open(yaml_path, "r", encoding="utf-8") as f:
        response["yamlFileContent"] = f.read()
    return response, 201

@app.route('/api/wikify_region', methods=['POST'])
@json_response
def wikify_region():
    project_path=request.args['project_path']
    data_path=request.args['data_path']
    sheet_name=request.args['sheet_name']
    #TOD0
    region = request.form["region"]
    context = request.form["context"]

    calc_params=CalcParams(project_path, data_path, sheet_name)
    cell_qnode_map, problem_cells = wikify(calc_params, region, context)

    wikifier_path = os.path.join(project_path, "wikify_region_output.csv")
    cell_qnode_map.to_csv(wikifier_path)
    project=apiProject.load(project_path)
    project.add_wikifier_file(wikifier_path)
    project.save()

    calc_params.wiki_paths=[wikifier_path]
    data = serialize_item_table(calc_params)

    if problem_cells:
        error_dict = {
            "errorCode": 400,
            "errorTitle": "Failed to wikify some cellsr",
            "errorDescription": "Failed to wikify: " + ",".join(problem_cells)
        }
        data['problemCells'] = error_dict
    else:
        data['problemCells'] = False

    return data, 200



#ALL THE GETS

@app.route('/api/table', methods=['GET'])
@json_response
def get_table():
    project_path=request.args['project_path']
    data_path=request.args['data_path']
    sheet_name=request.args['sheet_name']
    calc_params=CalcParams(project_path, data_path, sheet_name)
    tableData = table_data(calc_params)
    return {"tableData": tableData}, 200


@app.route('/api/wikifier', methods=['GET'])
@json_response
def get_wikifier():
    project_path=request.args['project_path']
    data_path=request.args['data_path']
    sheet_name=request.args['sheet_name']
    wikifier_paths=request.args.getlist['wikifier_path']
    calc_params=CalcParams(project_path, data_path, sheet_name, wikifier_paths=wikifier_paths)
    wikifierData=serialize_item_table(calc_params)
    return {"wikifierData":wikifierData}, 200

@app.route('/api/yaml', methods=['GET'])
@json_response
def get_yaml():
    project_path=request.args['project_path']
    data_path=request.args['data_path']
    sheet_name=request.args['sheet_name']
    yaml_path=request.args['yaml_path']
    wikifier_paths=request.args.getlist['wikifier_path']
    calc_params=CalcParams(project_path, data_path, sheet_name, yaml_path, wikifier_paths)
    yamlData=handle_yaml(calc_params)
    return {"yamlData":yamlData}, 200

@app.route('/api/download/<filetype>', methods=['GET'])
@json_response
def get_download(filetype):
    project_path=request.args['project_path']
    data_path=request.args['data_path']
    sheet_name=request.args['sheet_name']
    yaml_path=request.args['yaml_path']
    wikifier_paths=request.args.getlist['wikifier_path']
    calc_params=CalcParams(project_path, data_path, sheet_name, yaml_path, wikifier_paths)
    response = download(calc_params, filetype)
    return response, 200
    

@app.route('/api/qnode/<qid>', methods=['GET'])
@json_response
def get_qnode(qid):
    project_path=request.args['project_path']
    project=apiProject.load(project_path)
    label = get_qnode_label(qid, project.sparql_endpoint)
    return {"label": label}, 200


#we will eventually be deleting this and getting it from frontend, but for now...
@app.route('/api/cell/<col>/<row>', methods=['GET'])
@json_response
def get_cell_statement(col, row):
    project_path=request.args['project_path']
    data_path=request.args['data_path']
    sheet_name=request.args['sheet_name']
    yaml_path=request.args['yaml_path']
    wikifier_paths=request.args.getlist['wikifier_path']

    calc_params=CalcParams(project_path, data_path, sheet_name, yaml_path, wikifier_paths)
    data = get_cell(calc_params, col, row)
    return data, 200


#SOME MORE PUTS BUT IT'S ALL EDITING PRoJECTS:

@app.route('/api/settings', methods=['GET', 'PUT'])
@json_response
def put_settings():
    project_path=request.args['project_path']
    project=apiProject.load(project_path)

    if request.method=='POST':
        endpoint = request.form.get("endpoint", None)
        if endpoint:
            project.sparql_endpoint = endpoint
        warn = request.form.get("warnEmpty", None)
        if warn is not None:
            project.warn_for_empty_cells=warn.lower()=='true'
        title = request.form.get("title", None)
        if title:
            project.title = title
        project.save()
    
    response = {
        "endpoint": project.sparql_endpoint,
        "warnEmpty": project.warn_for_empty_cells,
        "title": project.title
    }

    return response, 200
    
    

######################OLD CODE

'''
@app.route('/api/project/<pid>/items', methods=['POST'])
@json_response
def add_item_definitions(pid):
    project = get_project(pid)
    in_file = file_upload_validator({"tsv"})
    i_f = ItemsFile.create(project, in_file)
    upload_item_defs(i_f.file_path)
    response = {}
    calc_params=get_calc_params(project)
    if calc_params:
        serialized_item_table = serialize_item_table(calc_params)
        response.update(serialized_item_table)
    return response, 200


@app.route('/api/project/<pid>/properties', methods=['POST'])
@json_response
def upload_properties(pid):
    project = get_project(pid)
    in_file = file_upload_validator({"json", "tsv"})
    return_dict = PropertiesFile.create(project, in_file)
    return return_dict, 200




@app.route('/api/wikifier/<pid>', methods=['POST'])
@json_response
def upload_wikifier_output(pid):
    """
    This function uploads the wikifier output
    :return:
    """
    project = get_project(pid)
    response = {"error": None}
    in_file = file_upload_validator({"csv"})

    wikifier_file = WikifierFile.create(project, in_file)
    calc_params=get_calc_params(project)
    if calc_params:
        serialized_item_table = serialize_item_table(calc_params)
        # does not go into field wikifierData but is dumped directly
        response.update(serialized_item_table)

    return response, 200


@app.route('/api/wikifier_service/<pid>', methods=['POST'])
@json_response
def wikify_region(pid):
    """
    This function calls the wikifier service to wikifiy a region, and deletes/updates wiki region file's results
    :return:
    """
    project = get_project(pid)
    action = request.form["action"]
    region = request.form["region"]
    context = request.form["context"]
    flag = int(request.form["flag"])
    if action == "wikify_region":
        if not project.current_file:
            raise web_exceptions.WikifyWithoutDataFileException(
                "Upload data file before wikifying a region")
        calc_params=get_calc_params(project)

        cell_qnode_map, problem_cells = wikify(calc_params, region, context)
        wf = WikifierFile.create_from_dataframe(project, cell_qnode_map)
        
        calc_params=get_calc_params(project)
        data = serialize_item_table(calc_params)

        if problem_cells:
            error_dict = {
                "errorCode": 400,
                "errorTitle": "Failed to wikify some cellsr",
                "errorDescription": "Failed to wikify: " + ",".join(problem_cells)
            }
            data['problemCells'] = error_dict
        else:
            data['problemCells'] = False

        return data, 200
    return {}, 404

@app.route('/api/yaml/<pid>', methods=['POST'])
@json_response
def upload_yaml(pid):
    """
    This function uploads and processes the yaml file
    :return:
    """
    project = get_project(pid)
    yaml_data = request.form["yaml"]
    response = {"error": None,
                "yamlRegions": None}
    if not string_is_valid(yaml_data):
        raise web_exceptions.InvalidYAMLFileException(
            "YAML file is either empty or not valid")
    else:
        if project.current_file:
            sheet = project.current_file.current_sheet
            yf = YamlFile.create_from_formdata(project, yaml_data, sheet)
            calc_params=get_calc_params(project)
            response['yamlRegions'] = highlight_region(calc_params)
        else:
            response['yamlRegions'] = None
            raise web_exceptions.YAMLEvaluatedWithoutDataFileException(
                "Upload data file before applying YAML.")

    return response, 200


'''




@app.route('/api/is-alive')
def is_alive():
    return 'Backend is here', 200


# We want to serve the static files in case the t2wml is deployed as a stand-alone system.
# In that case, we only have one webserver - Flask. The following two routes are for this.
# They are not used in dev (React's dev server is used to serve frontend assets), or in server deployment
# (nginx is used to serve static assets)
# @app.route('/')
# def serve_home_page():
#     return send_file(os.path.join(app.config['STATIC_FOLDER'], 'index.html'))


# @app.route('/<path:path>')
# def serve_static(path):
#     try:
#         return send_from_directory(app.config['STATIC_FOLDER'], path)
#     except NotFound:
#         return serve_home_page()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--debug':
            debug_mode = True
            print('Debug mode is on!')
        if sys.argv[1] == "--profile":
            from werkzeug.middleware.profiler import ProfilerMiddleware
            from app_config import UPLOAD_FOLDER

            app.config['PROFILE'] = True
            profiles_dir = os.path.join(UPLOAD_FOLDER, "profiles")
            if not os.path.isdir(profiles_dir):
                os.mkdir(profiles_dir)
            app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[
                100], profile_dir=profiles_dir)
        app.run(debug=True, port=13000)
    else:
        app.run(threaded=True, port=13000)
