import os
import re

from django.utils.text import slugify


def prepare_ocha_icons(download_path, templates_path):
    for icon_file_name in os.listdir(download_path):
        name = os.path.splitext(icon_file_name)[0]
        icon_name = slugify(name)

        with open(os.path.join(download_path, icon_file_name), 'r') as file:
            icon_content = file.read()
            icon_str_with_id = icon_content.replace('xmlns="http://www.w3.org/2000/svg"',
                                                    f'xmlns="http://www.w3.org/2000/svg" id="{icon_name}"')
            # replace all fill colors
            icon_str_with_fill = re.sub(r'fill="#[0-9a-fA-F]{6}"', 'fill="currentColor"', icon_str_with_id)
            icon_str_with_fill = icon_str_with_fill. \
                replace('style="fill: #000000;"', "")

            icon_template_path = os.path.join(templates_path, f"{icon_name}.svg")

        with open(icon_template_path, "w") as file:
            # Write data to the file
            file.write(icon_str_with_fill)

        print(f"Processed {icon_name}")
