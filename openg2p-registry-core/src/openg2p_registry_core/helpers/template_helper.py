import json
from jinja2 import Template, Environment
from pyld import jsonld
from typing import Dict
from openg2p_fastapi_common.service import BaseService

from ..helpers import MinioClient

class TemplateHelper(BaseService):
    def __init__(self):
        super().__init__()
        self.env = Environment()

    def get_template(self, minio_client: MinioClient, template_file_id: str) -> str:
        return minio_client.get_object(template_file_id).decode("utf-8")

    def get_jinja_template(self, minio_client: MinioClient, template_file_id: str) -> Template:
        template: Template = self.env.from_string(self.get_template(minio_client,template_file_id))
        return template
    
    def render_with_template(self, minio_client: MinioClient, template_file_id: str, data: Dict) -> Dict:
        expanded_data = jsonld.expand(data)
        jinja_template = self.get_jinja_template(minio_client, template_file_id)
        rendered_data: str = jinja_template.render(expanded=expanded_data)
        return json.loads(rendered_data)
