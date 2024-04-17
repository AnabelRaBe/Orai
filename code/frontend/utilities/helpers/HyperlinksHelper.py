import os
import regex as re
import json


class Hyperlinks:
    def __init__(self) -> None:
        pass

    def generate_references(self, result) -> list:
        content = json.loads(result['choices'][0]['messages'][0]['content'])
        preview = [source for source in content['citations']]
        return preview

    def add_hyperlinks(self, response, answer_without_followup: str, ) -> str:
        references = self.generate_references(response)

        urls = [source["url"] for source in references]
        regex = r'\[([^]]+)\]'

        results = re.findall(regex, answer_without_followup)
        references_ids = [re.findall("\d+", value)[0] for value in results]
        links = [urls[int(id)-1] for id in references_ids]

        container_name = os.environ.get('AZURE_BLOB_GLOBAL_DOCUMENTS_CONTAINER_NAME', 'documents2')
        for i, link in enumerate(links):
            modified_link = re.sub(f'/{re.escape(container_name)}/', '', link, count=1)
            answer_without_followup = answer_without_followup.replace(results[i], f"{modified_link}")

        return answer_without_followup    
    