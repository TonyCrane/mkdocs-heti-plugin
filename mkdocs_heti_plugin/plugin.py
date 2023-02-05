import os

from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.pages import Page
from mkdocs.utils import copy_file

from typing import Any, Dict, Optional, Literal

from .utils.heti import heti
from .utils.heti import (
    HETI_NON_CONTIGUOUS_ELEMENTS,
    HETI_SKIPPED_ELEMENTS,
    HETI_SKIPPED_CLASS,
)

PLUGIN_DIR = os.path.dirname(os.path.realpath(__file__))
HETI_CSS_DIR = os.path.join(PLUGIN_DIR, 'css/heti.css')

with open(HETI_CSS_DIR, 'r', encoding='utf-8') as file:
    HETI_CSS = file.read()

class HetiPlugin(BasePlugin):
    config_scheme = (
        ('enabled', config_options.Type(bool, default=True)),
        ('root_selector', config_options.Type(str, default="article")),
        ('disable_serve', config_options.Type(bool, default=True)),
        ('extra_skipped_class', config_options.Type(list, default=[])),
        ('extra_skipped_elements', config_options.Type(list, default=[])),
        ('extra_non_contiguous_elements', config_options.Type(list, default=[])),
    )

    enabled = True
    serve = False

    def on_startup(self, *, command: Literal['build', 'gh-deploy', 'serve'], dirty: bool) -> None:
        if command == "serve":
            self.serve = True

    def on_config(self, config: config_options.Config, **kwargs) -> Dict[str, Any]:
        if not self.enabled:
            return config
        
        if not self.config.get('enabled'):
            return config

        if self.config.get('disable_serve') and self.serve:
            return config
        
        config["extra_css"] = ["css/heti.css"] + config["extra_css"]
        HETI_SKIPPED_CLASS.extend(self.config.get('extra_skipped_class'))
        HETI_SKIPPED_ELEMENTS.extend(self.config.get('extra_skipped_elements'))
        HETI_NON_CONTIGUOUS_ELEMENTS.extend(self.config.get('extra_non_contiguous_elements'))
    
    def on_post_page(self, output: str, *, page: Page, config: config_options.Config) -> Optional[str]:
        if not self.enabled:
            return
        
        if not self.config.get('enabled'):
            return

        if self.config.get('disable_serve') and self.serve:
            return
        
        if hasattr(page, 'encrypted'):
            return
        return heti(output, self.config.get('root_selector'))

    def on_post_build(self, config: Dict[str, Any], **kwargs) -> None:
        if not self.enabled:
            return
        
        if not self.config.get('enabled'):
            return

        if self.config.get('disable_serve') and self.serve:
            return
        
        files = ["css/heti.css"]
        for file in files:
            dest_file_path = os.path.join(config["site_dir"], file)
            src_file_path = os.path.join(PLUGIN_DIR, file)
            assert os.path.exists(src_file_path)
            copy_file(src_file_path, dest_file_path)