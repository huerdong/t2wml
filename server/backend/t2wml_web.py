import json
from pathlib import Path
from ast import literal_eval
from collections import defaultdict
from t2wml.mapping.t2wml_handling import get_all_template_statements, resolve_cell
from t2wml.mapping.download import get_file_output_from_statements
from t2wml.spreadsheets.sheet import Sheet
from t2wml.utils.t2wml_exceptions import T2WMLException, TemplateDidNotApplyToInput
from t2wml.settings import t2wml_settings
from t2wml.api import set_sparql_endpoint, set_wikidata_provider, KnowledgeGraph
from t2wml.spreadsheets.sheet import Sheet
from t2wml.spreadsheets.conversions import column_index_to_letter
from t2wml.wikification.wikifier_service import WikifierService
from t2wml.wikification.item_table import Wikifier
from caching import CacheCellMapper
from app_config import DEFAULT_SPARQL_ENDPOINT
from wikidata_models import DatabaseProvider
from utils import query_wikidata_for_label_and_description

def wikify(region, filepath, sheet_name, context):
    ws=WikifierService()
    df, problem_cells= ws.wikify_region(region, filepath, sheet_name, context)
    return df, problem_cells

def update_t2wml_settings():
    set_sparql_endpoint(DEFAULT_SPARQL_ENDPOINT)
    set_wikidata_provider(DatabaseProvider(DEFAULT_SPARQL_ENDPOINT))
    t2wml_settings.update({
                "cache_data_files":True,
                "cache_results":True,
                #"wikidata_provider":DatabaseProvider(DEFAULT_SPARQL_ENDPOINT),
                #"sparql_endpoint":project.sparql_endpoint,
                #"storage_folder":UPLOAD_FOLDER
                })


def get_wikifier(project):
    #one day this will handle multiple wikifier files
    wikifier=Wikifier()
    if project.wikifier_file:
        wikifier.add_file(project.wikifier_file.file_path)
    return wikifier

def get_kg(data_sheet, cell_mapper, project):
    wikifier=get_wikifier(project)
    sheet=Sheet(data_sheet.data_file.file_path, data_sheet.name)
    kg=KnowledgeGraph.generate(cell_mapper, sheet, wikifier)
    return kg

def download(data_sheet, yaml_file, project, filetype, project_name=""):
    cell_mapper=CacheCellMapper(data_sheet, yaml_file)
    response=dict()
    kg=cell_mapper.result_cacher.get_kg()
    if not kg:
        kg=get_kg(data_sheet, cell_mapper, project)
    
    response["data"]=get_file_output_from_statements(kg, filetype)
    response["error"]=None
    response["internalErrors"] = kg.errors if kg.errors else None
    return response

def highlight_region(data_sheet, yaml_file, project):
    cell_mapper=CacheCellMapper(data_sheet, yaml_file)
    highlight_data, statement_data, errors=cell_mapper.result_cacher.get_highlight_region()
    if highlight_data:
        highlight_data['error']=errors if errors else None
        highlight_data['cellStatements']=statement_data
        return highlight_data

    highlight_data = {"dataRegion": set(), "item": set(), "qualifierRegion": set(), 'referenceRegion': set(), 'error': dict()}
    kg=get_kg(data_sheet, cell_mapper, project)
    statement_data=kg.statements
    errors=kg.errors
    for cell in statement_data:
        highlight_data["dataRegion"].add(cell)
        statement = statement_data[cell]
        item_cell=statement.get("cell", None)
        if item_cell:
            highlight_data["item"].add(item_cell)
        qualifiers = statement.get("qualifier", None)
        if qualifiers:
            for qualifier in qualifiers:
                qual_cell=qualifier.get("cell", None)
                if qual_cell:
                    highlight_data["qualifierRegion"].add(qual_cell)
    
        references = statement.get("reference", None)
        if references:
            for ref in references:
                ref_cell=ref.get("cell", None)
                if ref_cell:
                    highlight_data["referenceRegion"].add(ref_cell)

    highlight_data['dataRegion'] = list(highlight_data['dataRegion'])
    highlight_data['item'] = list(highlight_data['item'])
    highlight_data['qualifierRegion'] = list(highlight_data['qualifierRegion'])
    highlight_data['referenceRegion'] = list(highlight_data['referenceRegion'])
    cell_mapper.result_cacher.save(highlight_data, statement_data, errors)
    
    highlight_data['error']=errors if errors else None
    highlight_data['cellStatements']=statement_data
    return highlight_data

def get_cell(data_sheet, yaml_file, project, col, row):
    wikifier=get_wikifier(project)
    cell_mapper=CacheCellMapper(data_sheet, yaml_file)
    sheet=Sheet(data_sheet.data_file.file_path, data_sheet.name)
    try:
        statement, errors= resolve_cell(cell_mapper, sheet, wikifier, col, row)
        data = {'statement': statement, 'internalErrors': errors if errors else None, "error":None}
    except TemplateDidNotApplyToInput as e:
        data=dict(error=e.errors)
    except T2WMLException as e:
        data=dict(error=e.error_dict)
    return data

def table_data(data_file, sheet_name=None):
    sheet_names= [sheet.name for sheet in data_file.sheets]
    if sheet_name is None:
        sheet_name = sheet_names[0]

    data=sheet_to_json(data_file.file_path, sheet_name)
    
    is_csv = True if data_file.extension.lower() == ".csv" else False

    return {
            "filename":data_file.name,
            "isCSV":is_csv,
            "sheetNames": sheet_names,
            "currSheetName": sheet_name,
            "sheetData": data
        }


def handle_yaml(sheet, project):
    if sheet.yaml_file:
        yaml_file=sheet.yaml_file
        response=dict()
        with open(yaml_file.file_path, "r") as f:
            response["yamlFileContent"]= f.read()
        response['yamlRegions'] = highlight_region(sheet, yaml_file, project)
        return response
    return None


def sheet_to_json(data_file_path, sheet_name):
    sheet=Sheet(data_file_path, sheet_name)
    data=sheet.data.copy()
    json_data = {'columnDefs': [{'headerName': "", 'field': "^", 'pinned': "left"}], 
                'rowData': []}
    #get col names
    col_names=[]
    for i in range(len(sheet.data.iloc[0])):
        column = column_index_to_letter(i)
        col_names.append(column)
        json_data['columnDefs'].append({'headerName': column, 'field': column})
    #rename cols
    data.columns=col_names
    #rename rows
    data.index+=1
    #get json
    json_string=data.to_json(orient='table')
    json_dict=json.loads(json_string)
    initial_json=json_dict['data']
    #add the ^ column
    for i, row in enumerate(initial_json):
        row["^"]=str(i+1)
    #add to the response
    json_data['rowData']=initial_json
    return json_data



def serialize_item_table(project, sheet):
    wikifier=get_wikifier(project)
    item_table=wikifier.item_table
    serialized_table = {'qnodes': defaultdict(defaultdict), 'rowData': list(), 'error': None}
    items_to_get = set()

    for context in item_table.lookup_table:
        context_table=item_table.lookup_table[context]
        for str_key in context_table:
            item=context_table[str_key]
            tuple_key=literal_eval(str_key)
            column, row_str, value = tuple_key

            col=row=cell=''
            if column:
                col = column_index_to_letter(int(column))
            if row_str:
                row = str(int(row_str) + 1)
            if column and row_str:
                cell = col+row

            serialized_table['qnodes'][cell][context]=  {"item": item}
            row_data = {
                        'context': context,
                        'col': col,
                        'row': row,
                        'value': value,
                        'item': item
                    }


            items_to_get.add(item)
            serialized_table['rowData'].append(row_data)

    labels_and_descriptions = query_wikidata_for_label_and_description(list(items_to_get))
    for i in range(len(serialized_table['rowData'])):
        item_key=serialized_table['rowData'][i]['item']
        if item_key in labels_and_descriptions:
            label=labels_and_descriptions[item_key]['label']
            desc=labels_and_descriptions[item_key]['desc']
            serialized_table['rowData'][i]['label'] = label
            serialized_table['rowData'][i]['desc'] = desc

        for cell, con in serialized_table["qnodes"].items():
            for context, context_desc in con.items():
                item_key=context_desc['item']
                if item_key in labels_and_descriptions:
                    label=labels_and_descriptions[item_key]['label']
                    desc=labels_and_descriptions[item_key]['desc']
                    serialized_table['qnodes'][cell][context]['label'] = label
                    serialized_table['qnodes'][cell][context]['desc'] = desc
    return serialized_table