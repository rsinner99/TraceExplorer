"""
This module helps to create a graphical representation
of the hierarchical span structure in html.
"""

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
