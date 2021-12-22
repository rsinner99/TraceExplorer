"""
This module helps to create a graphical representation
of the hierarchical span structure in html.
"""

import os
from jinja2 import Environment, FileSystemLoader

root = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(root, 'templates')
env = Environment( loader = FileSystemLoader(templates_dir) )


def create_trace_html(traces):
    """Creates a HTML report for each Trace in the list."""
    for trace in traces:
        if trace.error_count == 0:
            continue
        spans = sorted(trace.spans, key=lambda span: span.rating, reverse=True)
        spans = [span.__dict__() for span in spans if span.error]
        graph = html_graph(trace.root_span)
        strands = [[span.cause for span in strand] for strand in trace.get_error_strands()]
        template = env.get_template('spans.html')
        output = template.render(spans=spans, trace=trace.__dict__(), graph=graph, strands=strands)
        with open(trace.filename, 'w', encoding='utf-8') as file:
            file.write(output)

def create_szenario_html(szenarios):
    """Creates a file with szenarios details."""
    result = [szenario.__dict__() for szenario in szenarios]
    filename = 'szenarios.html'
    template = env.get_template('szenarios.html')
    output = template.render(szenarios=result)
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(output)

def walk_tree(span):
    """Recursive function to create html objects of the spans children."""
    result = []
    if span.children:
        result.append('<ul>\n')
        children = sorted(span.children, key=lambda child: child.start_time)
        for child in children:
            if child.error:
                result.append(
                    f'<li> <span style="color:red">{child.operation_name}: {child.cause}</span>\n')
            else:
                result.append(f'<li> <span>{child.operation_name}</span>\n')
            result.extend(walk_tree(child))
            result.append('</li>\n')
        result.append('</ul>\n')
    return result

def html_graph(root_span):
    """Return a string which defines a graph representation in html."""
    result = ['<ul class="tree">\n']
    result.append(f'<li> <span>{root_span.operation_name}</span>\n')
    result.extend(walk_tree(root_span))
    result.append('</li>\n</ul>\n')
    return ''.join(result)
