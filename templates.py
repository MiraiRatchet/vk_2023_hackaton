import re


def get_str_from_html(html):
    with open(html, 'r', encoding='utf-8') as file:
        result_html = file.read()
    return result_html


def get_template(html, **params):
    result_html = get_str_from_html(html)

    if re.search(r'{%\s*for\s+(\w+)\s+in\s+\w+\s*%}', result_html):
        print("here")
        result_html = parser_for_loop(result_html, **params)

    if re.search(r'%if', result_html): ### тут
        print("Will be IF")
        result_html = parse_html_with_if_condition(result_html, **params)
    else:
        print("NO IF")

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


def parse_html_with_conditions(html, parameters):
    # Используем регулярные выражения для поиска блоков if и endif
    pattern_if = re.compile(r'{%if\s(.*?)%}(.*?){%(else|endif)%}', re.DOTALL)
    pattern_all_if = re.compile(r'{%if(.*?){%endif%}', re.DOTALL)
    pattern_else = re.compile(r'{%else%}(.*?){%endif%}', re.DOTALL)

    match = pattern_if.search(html)
    if eval(match.group(1), parameters):
        replacement_text = match.group(2)
        modified_html = pattern_all_if.sub(replacement_text, html)
        modified_html = parse_html_simple(modified_html, parameters)
        return modified_html
    match = pattern_else.search(html)
    if match:
        replacement_text = match.group(1)
        modified_html = pattern_all_if.sub(replacement_text, html)
        modified_html = parse_html_simple(modified_html, parameters)
        return modified_html
    return html
