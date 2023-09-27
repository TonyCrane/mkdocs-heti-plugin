import os
import re

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

        # **temporarily fix**
        # by replacing <kbd> tag with sth. like HETIkbdSTART0HETIkbdEND and remembering the content
        # then replace them after heti's processing
        # so is .arithmatex
        kbd_content = []
        while match := re.search(r"<kbd>(.*?)</kbd>", output):
            kbd_content.append(match.group(1))
            output = output[:match.start()] + f"HETIkbdSTART{len(kbd_content) - 1}HETIkbdEND" + output[match.end():]
        math_content = []
        while match := re.search(r"<span class=\"arithmatex\">(.*?)</span>", output):
            math_content.append(match.group(1))
            output = output[:match.start()] + f"HETImathSTART{len(math_content) - 1}HETImathEND" + output[match.end():]
        
        html = heti(output, self.config.get('root_selector'))

        for i in range(len(kbd_content)):
            html = html.replace(f"HETIkbdSTART{i}HETIkbdEND", f"<kbd>{kbd_content[i]}</kbd>")
        for i in range(len(math_content)):
            html = html.replace(f"HETImathSTART{i}HETImathEND", f"<span class=\"arithmatex\">{math_content[i]}</span>")
        
        return html

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