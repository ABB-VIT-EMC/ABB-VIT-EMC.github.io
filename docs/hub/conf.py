project = "ABB SpA Vittuone Laboratory Software Documentation"
author = "Thanapong Chuangyanyong"
copyright = "ABB SpA"

extensions = []
templates_path = ["_templates"]
exclude_patterns = []

html_theme = "furo"
html_title = "ABB VIT EMC Documentation"
html_theme_options = {
    "source_repository": "https://github.com/ABB-VIT-EMC/ABB-VIT-EMC.github.io/",
    "source_branch": "main",
    "source_directory": "docs/hub/",
    "light_css_variables": {
        "color-brand-primary": "#c00000",
        "color-brand-content": "#9c0000",
    },
    "dark_css_variables": {
        "color-brand-primary": "#ff8a8a",
        "color-brand-content": "#ffb3b3",
    },
}
