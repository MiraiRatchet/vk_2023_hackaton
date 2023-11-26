import re


def get_str_from_html(html):
    with open(html, 'r', encoding='utf-8') as file:
        result_html = file.read()
    return result_html


def get_template(html, **params):
    result_html = get_str_from_html(html)

    if re.search(r'{%\s*for\s+(\w+)\s+in\s+\w+\s*%}', result_html):
        #print("here")
        result_html = parser_for_loop(result_html, **params)

    if re.search(r'%if', result_html): ### тут
        #print("Will be IF")
        result_html = parse_html_with_if_condition(result_html, **params)
    else:
        pass #print("NO IF")

    if re.search(r'{{(.*?)}}', result_html):
        result_html = substitution(result_html, **params)

    return result_html


def substitution(html, **params):
    for param_name, param_value in params.items():
        pattern = re.compile(r'{{' + re.escape(param_name) + '}}')

        html = re.sub(pattern, str(param_value), html)

    return html


def parser_for_loop(html_str, **param_list):
    result_html = html_str

    for loop_name, loop_data in param_list.items():
        param_match = re.finditer(r'{%\s*for\s+(\w+)\s+in\s+\w+\s*%}', html_str)

        for param_iter in param_match:
            param = param_iter.group(1).strip()

            pattern = re.compile(r'{%\s*for\s*' + param + r'\s*in\s*' + loop_name + r'.*?%}([\s\S]*?)' + r'{%\s*endfor\s*%}', re.DOTALL)
            matches = re.finditer(pattern, result_html)

            for match in matches:

                loop_content = match.group(1).strip()
                loop_result = get_sub_loop(loop_content, param_list[loop_name], param)
                result_html = result_html.replace(match.group(), loop_result)

    return result_html


def get_sub_loop(loop_content, param_list, param):
    temp = {}
    loop_result = ''
    for values in param_list:
        for key in values.keys():
            temp[param + "['" + key + "']"] = values[key]
        loop_result += "\n" + substitution(loop_content, **temp)
    return loop_result


def parse_html_with_if_condition(html, parameters):
    pattern_if = re.compile(r'{%if\s(.*?)%}(.*?){%endif%}', re.DOTALL)

    def parse_if_block(match):
        condition = match.group(1)
        block_content = match.group(2)

        # Проверяем выполнение условия
        if eval(condition, parameters):
            # Применяем функцию подстановки значений к блоку внутри if
            return substitution(block_content, parameters)
        else:
            return ''

            # Применяем функцию parse_if_block ко всем блокам if в HTML

    html = re.sub(pattern_if, parse_if_block, html)

    return html