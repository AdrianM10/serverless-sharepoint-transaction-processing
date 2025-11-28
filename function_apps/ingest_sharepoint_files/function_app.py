import azure.functions as func

from ingest_sharepoint_files_blueprint import ingest_sp_bp

app = func.FunctionApp()

app.register_functions(ingest_sp_bp)
