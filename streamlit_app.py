import streamlit as st
import pandas as pd
import os
import warnings 
import glob
from nbconvert import PythonExporter
import nbformat
import glob
import importlib.util
import matplotlib.pyplot as plt
import requests
import json

warnings.filterwarnings('ignore')

storage_file = 'input_storage.json'

# Function to load inputs from the storage file
def load_inputs():
    if os.path.exists(storage_file):
        with open(storage_file, 'r') as f:
            return json.load(f)
    return {}

# Function to save inputs to the storage file
def save_inputs(inputs):
    with open(storage_file, 'w') as f:
        json.dump(inputs, f)

if 'inputs' not in st.session_state:
    st.session_state.inputs = load_inputs()

input_fields = {
    'vd_file_path': 'Enter vd file path',
    'folder_path': "Enter folder path",
    'figure_path': "Enter file name",
}

# Initialize inputs in session state if not already set
for key in input_fields.keys():
    if key not in st.session_state.inputs:
        st.session_state.inputs[key] = ""


# def convert_notebook_to_script(notebook_path, script_path):
#     """Convert Jupyter notebook to Python script."""
#     with open(notebook_path, 'r', encoding='utf-8') as f:
#         notebook_content = nbformat.read(f, as_version=4)
#     exporter = PythonExporter()
#     script, _ = exporter.from_notebook_node(notebook_content)
#     with open(script_path, 'w', encoding='utf-8') as f:
#         f.write(script)

# def import_functions_from_script(script_path):
#     """Import functions starting with 'func_' from a Python script."""
#     module_name = os.path.splitext(os.path.basename(script_path))[0]
#     spec = importlib.util.spec_from_file_location(module_name, script_path)
#     module = importlib.util.module_from_spec(spec)
#     spec.loader.exec_module(module)

#     functions = {}
#     for name in dir(module):
#         if name.startswith("func_"):
#             func = getattr(module, name)
#             if callable(func):
#                 functions[name] = func
#     return functions

def inverse_process_string_list(input_list):
        processed_list = []
        for input_string in input_list:
            # Prepend 'func_' to the entire string
            reconstructed_string = 'func_' + '_'.join(input_string.split())
            processed_list.append(reconstructed_string)
        return processed_list

def get_python_files_from_github_folder(folder_url):
    """Retrieve and execute .py files from a GitHub folder."""
    # Extract the API URL to list contents of the folder
    folder_api_url = folder_url.replace('https://github.com/', 'https://api.github.com/repos/')
    folder_api_url = folder_api_url.replace('tree/main/', 'contents/')

    # Get the list of files in the folder
    response = requests.get(folder_api_url)
    
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve folder contents: {response.status_code}")

    contents = response.json()
    
    # Filter out .py files
    py_files = [item for item in contents if item['name'].endswith('.py') and item['type'] == 'file']

    if not py_files:
        raise Exception("No Python (.py) files found in the folder.")
    
    # Process each .py file
    all_functions = {}
    for file_info in py_files:
        file_url = file_info['download_url']
        # print(file_url)  # Direct URL to the raw file content
        # print(f"Processing file: {file_info['name']}")
        f = import_functions_from_github(file_url)
        all_functions.update(f)
    return all_functions

def import_functions_from_github(file_url):
    """Import functions starting with 'func_' from a Python script on GitHub."""
    # Fetch the script content from GitHub
    response = requests.get(file_url)
    
    if response.status_code != 200:
        raise Exception(f"Failed to download script: {response.status_code}")
    
    script_content = response.text

    # Create a temporary module
    module_name = os.path.splitext(os.path.basename(file_url))[0]
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    module = importlib.util.module_from_spec(spec)
    
    # Execute the script content within this module
    exec(script_content, module.__dict__)
    
    # Import and return all functions starting with 'func_'
    functions = {name: obj for name, obj in module.__dict__.items() if callable(obj) and name.startswith('func_')}
    # print(functions)
    return functions

####################################
################################
############################


st.set_page_config(page_title='KINESYS dashboard', page_icon=':bar_chart:',layout='wide')
# st.set_option('server.maxUploadSize', 400)

st.title(':bar_chart: KINESYS Results')

tab1, tab2 = st.tabs(["**VD to CSV**", "**Figures display**"])

# sidebar_placeholder = st.sidebar.empty()


# st.markdown('<style>div.block-container{padding-top:1rem;}<style>',unsafe_allow_html=True)

# folder_path_csv = r'G:\Departement_ R141\Modelisation TIMES\KINESYS output\VD to csv'
with tab1:
    col1, col2, col3 = st.columns([3, 1, 3], vertical_alignment='center')
    
    fl = st.file_uploader(":page_facing_up: Choose VD file:", type=['vd'])
    with col1:
        st.session_state.inputs['vd_file_path'] = st.text_input(':open_file_folder: Enter the WorkTIMES directory'
                                                               , st.session_state.inputs['vd_file_path'])
        directory = st.session_state.inputs['vd_file_path']

        # directory = st.text_input(':open_file_folder: Enter the WorkTIMES directory')
    with col2:
        st.markdown(
            """
            <div style='text-align: center; font-size: 36px; line-height: 1.5;'>&rarr;</div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        # storage_input = 'input_storage.json'
        # if 'folder_path' not in st.session_state:
        #     st.session_state.folder_path = load_input(storage_input)

        # # Text input for the folder path
        # output_data_in = st.text_input(":open_file_folder: Enter the folder for CSV files", st.session_state.folder_path)

        # if output_data_in != st.session_state.folder_path:
        #     st.session_state.folder_path = output_data_in
        #     save_input(output_data_in,storage_input)
        st.session_state.inputs['folder_path'] = st.text_input(':open_file_folder: Enter the folder for CSV files'
                                                               , st.session_state.inputs['folder_path'])
        output_data_in = st.session_state.inputs['folder_path']
        # output_data_in = st.text_input(':open_file_folder: Enter the folder for CSV files')        

    if fl and directory and output_data_in:
        filename = fl.name
        directory = directory.replace('\\','/')

        file_path = directory + '/' + filename
        # st.write(file_path)

        folder_url_csv = 'https://github.com/BenjaminTrouve/kinesys-results-tool/tree/main/VD%20to%20csv'
        function_to_csv  = get_python_files_from_github_folder(folder_url_csv)
        # ipynb_files = glob.glob(os.path.join(folder_path_csv, '*.ipynb'))
        # ipynb_file_names = [os.path.basename(file) for file in ipynb_files]

        # all_functions = {}
        # for filename_csv in ipynb_file_names:
        #     # notebook_path = os.path.join(folder_path_csv, filename_csv)
        #     # script_path = os.path.join(folder_path_csv, filename_csv.replace(".ipynb", ".py"))
        #     # convert_notebook_to_script(notebook_path, script_path)
        #     # function_vd_csv = import_functions_from_script(script_path)

        str_keys = [str(key) for key in function_to_csv.keys()]
        function_to_call =  function_to_csv[str_keys[0]]
        function_to_call(file_path,output_data_in)

        st.write('Converted !!!')


with tab2:
    st.markdown('**STEP 1: Set the directory for the input data and figures output**')
    col1, col2, col3 = st.columns([3, 1, 3], vertical_alignment='center')
    with col1:
        # storage_input = 'input_storage.json'
        # # Load the stored input when the app starts
        # if 'folder_path' not in st.session_state:
        #     st.session_state.folder_path = load_input(storage_input)

        # # Text input for the folder path
        # input_path = st.text_input(":open_file_folder: Enter the path for in input data", st.session_state.folder_path)

        # if input_path != st.session_state.folder_path:
        #     st.session_state.folder_path = input_path
        #     save_input(input_path,storage_input)
        
        st.session_state.inputs['folder_path'] = st.text_input(":open_file_folder: Enter the path for in input data"
                                                               , st.session_state.inputs['folder_path'])
        input_path = st.session_state.inputs['folder_path']
    with col2:
        st.markdown(
            """
            <div style='text-align: center; font-size: 36px; line-height: 1.5;'>&rarr;</div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        # storage_output = 'output_storage.json'
        # # Load the stored input when the app starts
        # if 'folder_path' not in st.session_state:
        #     st.session_state.folder_path = load_input(storage_output)

        # # Text input for the folder path
        # output_path = st.text_input(":open_file_folder: Enter figure output folder", st.session_state.folder_path)

        # if output_path != st.session_state.folder_path:
        #     st.session_state.folder_path = output_path
        #     save_input(output_path,storage_output)
        st.session_state.inputs['figure_path'] = st.text_input(":open_file_folder: Enter figure output folder"
                                                               , st.session_state.inputs['figure_path'])
        output_path = st.session_state.inputs['figure_path']
        # output_path = st.text_input(":open_file_folder: Enter figure output folder")


    st.markdown('**STEP 2: Choose the reference and the scenario run based on the running date**')
    col4, col5 = st.columns((2))
    start_date = '2024-05-28'
    end_date = '2024-06-14'
    date_series = pd.date_range(start=start_date, end=end_date,freq='D')

    ref_date = date_series.min()
    scen_date = date_series.max()

    with col4:
        date_ref = pd.to_datetime(st.date_input(':date: Reference date', ref_date))
        date_ref_ddmm = date_ref.strftime('%d%m')

    with col5:
        date_scen = pd.to_datetime(st.date_input(':date: Scenario date', scen_date))
        date_scen_ddmm = date_scen.strftime('%d%m')

    st.markdown('**STEP 3: Choose figure to display!**')

    def scenario_param(date_ref, date_scen,input_path,output_path):
        date_list = [date_ref, date_scen]
        run_name_ref = f'nze~0004_{date_list[0]}'
        run_name_scen = f'nze~0004_{date_list[1]}'
        folder_path = input_path.replace('\\','/')
        file_path_ref = os.path.join(folder_path,run_name_ref) + '/'
        file_path_scen = os.path.join(folder_path,run_name_scen) + '/'
        output_path1 = output_path.replace('\\','/')
        output_folder = os.path.join(output_path1,run_name_scen) + '/'


        os.makedirs(output_folder, exist_ok=True)
        return run_name_ref, run_name_scen, file_path_ref, file_path_scen, output_folder

    if input_path and output_path and date_ref_ddmm and date_scen_ddmm:
        run_name_ref, run_name_scen, file_path_ref, file_path_scen, output_folder = scenario_param(date_ref_ddmm,date_scen_ddmm,input_path,output_path)



    # folder_path = r'C:\Users\trouvebe\Desktop\Thesis\Chapter 1\Python functions\Kinesys post-processing\Analysis'
    # folder_path = r'G:\Departement_ R141\Modelisation TIMES\KINESYS output\Functions'
    # url = 'https://api.github.com/repos/BenjaminTrouve/Kinesys_functions/contents/Analysis'
    # # Send the request
    # response = requests.get(url)
    # if response.status_code == 200:
    #     folder_path = response.json()
    # py_files = [item for item in contents if item['name'].endswith('.py') and item['type'] == 'file']

    # Process all .ipynb files in the folder
    # ipynb_files = glob.glob(os.path.join(folder_path, '*.ipynb'))
    # ipynb_file_names = [os.path.basename(file) for file in ipynb_files]

    # all_functions = {}
    # for filename in ipynb_file_names:
    #     notebook_path = os.path.join(folder_path, filename)
    #     script_path = os.path.join(folder_path, filename.replace(".ipynb", ".py"))
    #     convert_notebook_to_script(notebook_path, script_path)
    #     functions = import_functions_from_script(script_path)
    #     all_functions.update(functions)

    folder_url = 'https://github.com/BenjaminTrouve/kinesys-results-tool/tree/main/Analysis'
    all_functions  = get_python_files_from_github_folder(folder_url)

    def process_string_list(input_list):
        processed_list = []
        for input_string in input_list:
            substrings = input_string.split('_')
            filtered_substrings = [s for s in substrings if "func" not in s]
            result_string = ' '.join(filtered_substrings)
            processed_list.append(result_string)
        return processed_list


    # st.sidebar.title('Figure selection')
    function_choice = st.multiselect('Choose your figures:', process_string_list(all_functions.keys()))

    function_choice_list = inverse_process_string_list(function_choice)

    if st.button("Run Selected Functions"):
        for func_name in function_choice_list:
            func =  all_functions[func_name]
    # if function_choice:
    #     func = all_functions[function_choice_list[0]]
            st.set_option('deprecation.showPyplotGlobalUse', False) 
            # figure_func = function_choice[0]
            fig = func(file_path_scen,file_path_ref, run_name_scen,run_name_ref,output_folder)
            # for f in fig:
            st.pyplot(fig)
            plt.close(fig)

save_inputs(st.session_state.inputs)

