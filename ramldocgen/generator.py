from xml.sax.saxutils import escape
import pyraml.parser as ramlparser
from .inlines import highlight_inline_js, api_doc_inline_css
from collections import OrderedDict
import re
import sys
import json

no_short_close = ['div', 'span', 'script']


def idfirst(od):
    res = OrderedDict()
    if 'id' in od:
        res['id'] = od['id']
    for k, v in od.items():
        if k == 'id':
            continue
        res[k] = v
    return res


class HTMLNode(object):
    def __init__(self, name, attributes={}, may_short_close=None):
        self.name = name
        self.attributes = idfirst(OrderedDict([(k, attributes[k]) for k in sorted(attributes)]))
        self.children = []
        if may_short_close is None:
            self.may_short_close = name not in no_short_close
        else:
            self.may_short_close = may_short_close
        self._indent = 0
        self._pretty = False
        self._debug = False

    def append(self, tag):
        if not isinstance(tag, HTMLNode):
            tag = HTMLText(str(tag))
        self.children.append(tag)
        return tag

    def prepend(self, tag):
        if not isinstance(tag, HTMLNode):
            tag = HTMLText(str(tag))
        self.children.insert(0, tag)
        return tag

    def extend(self, tags):
        for a in tags:
            self.append(a)

    def render(self, indent=None, pretty=None):
        i = self._indent
        p = self._pretty
        if indent is not None:
            self._indent = indent
        if pretty is not None:
            self._pretty = pretty
        ret = str(self)
        self._indent = i
        self._pretty = p
        return ret

    def copy(self):
        dest = HTMLNode(self.name)
        dest.attributes = self.attributes.copy()
        dest.children = [c.copy() for c in self.children]
        dest.may_short_close = self.may_short_close
        return dest

    def copy_contents(self):
        return [c.copy() for c in self.children]

    def is_onlytext(self):
        for el in self.children:
            if not isinstance(el, HTMLText):
                return False
        return True

    def __str__(self):
        indent = self._indent * '\t' if self._pretty else ''
        attrib = ''
        if len(self.attributes) > 0:
            attrib = ' {0}'.format(' '.join(["{0}=\"{1}\"".format(k, escape(self.attributes[k])) for k in self.attributes]))
        if len(self.children) == 0 and self.may_short_close:
            return "{2}<{0}{1} />".format(self.name, attrib, indent)
        else:
            if self._pretty:
                cjoin = '\n'
            else:
                cjoin = ''
            br = '\n' if self._pretty and not self.is_onlytext() else ''
            if self._debug:
                print("<{0}>{1}</{0}>".format(self.name, cjoin.join([c.render(self._indent + 1, self._pretty) for c in self.children]), attrib, indent, br, indent if br != '' else ''), file=sys.stderr)
            return "{3}<{0}{2}>{4}{1}{4}{5}</{0}>".format(self.name, cjoin.join([c.render(self._indent + 1, self._pretty) for c in self.children]), attrib, indent, br, indent if br != '' else '')


def urlify(text):
    return re.sub(r'http(?:s?)://\S+', r'<a href="\g<0>" target="_blank">\g<0></a>', text)


class HTMLText(HTMLNode):
    def __init__(self, text):
        self.text = text
        self._indent = 0
        self._pretty = False

    def copy(self):
        return HTMLText(self.text)

    def __str__(self):
        return urlify(escape(self.text)).replace('\n', '<br />')


class HTMLScript(HTMLNode):
    def __init__(self, text):
        self.text = text
        self._indent = 0
        self._pretty = False

    def copy(self):
        return HTMLScript(self.text)

    def __str__(self):
        return self.text


class inline(HTMLScript):
    def js(self):
        tag = HTMLNode('script', {'type': 'text/javascript'})
        tag.append(self)
        return tag

    def css(self):
        tag = HTMLNode('style', {'type': 'text/css'})
        tag.append(self)
        return tag


class src(HTMLScript):
    def js(self):
        tag = HTMLNode('script', {'type': 'text/javascript', 'src': self.text})
        return tag

    def css(self):
        tag = HTMLNode('link', {'rel': 'stylesheet', 'href': self.text})
        return tag


class meta(object):
    def __init__(self, content, name=None, httpequiv=None):
        self.node = HTMLNode('meta')
        if name is not None:
            self.node.attributes['name'] = name
        if httpequiv is not None:
            self.node.attributes['http-equiv'] = httpequiv
        self.node.attributes['content'] = content

    def meta(self):
        return self.node

    def __str__(self):
        return str(self.node)


class HTMLTagHead(HTMLNode):
    def __init__(self):
        super(HTMLTagHead, self).__init__("head")
        self.meta = []
        self.css = []
        self.title = None
        self.js = []

    def add_inline_js(self, data):
        self.js.append(inline(data))

    def add_inline_css(self, data):
        self.css.append(inline(data))

    def add_external_js(self, url):
        self.js.append(src(url))

    def add_external_css(self, url):
        self.css.append(src(url))

    def add_named_meta(self, name, content):
        self.meta.append(meta(content, name=name))

    def add_equiv_meta(self, httpequiv, content):
        self.meta.append(meta(content, httpequiv=httpequiv))

    def __str__(self):
        self.attributes = {}
        self.children = []
        if self.title is not None:
            t = HTMLNode('title')
            t.append(HTMLText(self.title))
            self.children.append(t)
        self.children.extend([s.meta() for s in self.meta])
        self.children.extend([s.css() for s in self.css])
        self.children.extend([s.js() for s in self.js])
        ret = super(HTMLTagHead, self).__str__()
        return ret

    def copy(self):
        dest = HTMLTagHead()
        dest.meta = self.meta.copy()
        dest.css = self.css.copy()
        dest.title = self.title
        dest.js = self.js.copy()
        return dest

class HTML(HTMLNode):
    def __init__(self):
        super(HTML, self).__init__('html')
        self.head = HTMLTagHead()
        self.body = HTMLNode('body')

    def __str__(self):
        self.children = [self.head, self.body]
        return super(HTML, self).__str__()

    def copy(self):
        dest = HTML()
        dest.head = self.head.copy()
        dest.body = self.body.copy()
        return dest

def classify(name):
    return re.sub(r'/+|\{|\}', '_', re.sub('[^a-zA-Z0-9/{}]', '', name.lstrip('/')))

def collect(root, base=''):
    root._collect_path = base
    elems = [root]
    if root.resources is not None:
        for e in root.resources:
            elems.extend(collect(root.resources[e], ''.join([base, e])))
    return elems

class Generator(object):
    def __init__(self, file):
        self.raml = ramlparser.load(file)

    def generate(self):
        doc = HTML()
        doc.head.title = self.raml.title

        # Add meta tags, CSS and JS sources.
        doc.head.add_equiv_meta('X-UA-Compatible', 'IE=edge')
        doc.head.add_equiv_meta('Content-Type', 'text/html; charset=utf-8')
        doc.head.add_external_css('https://netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css')
        doc.head.add_external_css('https://cdnjs.cloudflare.com/ajax/libs/highlight.js/8.1/styles/default.min.css')
        doc.head.add_inline_css(api_doc_inline_css)
        doc.head.add_external_js('https://code.jquery.com/jquery-1.11.0.min.js')
        doc.head.add_external_js('https://netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js')
        doc.head.add_external_js('https://cdnjs.cloudflare.com/ajax/libs/highlight.js/8.1/highlight.min.js')
        doc.head.add_inline_js(highlight_inline_js)

        # Body container and layout.
        doc.body.attributes['data-spy'] = 'scroll'
        doc.body.attributes['data-target'] = '#sidebar'
        container = doc.body.append(HTMLNode('div', {'class': 'container'}))
        row = container.append(HTMLNode('div', {'class': 'row'}))
        information_wrapper = row.append(HTMLNode('div', {'class': 'col-md-9', 'role': 'main'}))
        legend = row.append(HTMLNode('div', {'class': 'col-md-3'})).append(HTMLNode('div', {'id': 'sidebar', 'class': 'hidden-print affix', 'role': 'complementary'})).append(HTMLNode('ul', {'class': 'nav nav-pills nav-stacked'}))
        legend_api_wrapper = legend.append(HTMLNode('li'))
        legend_api_wrapper.append(HTMLNode('a', {'href': '#_api_endpoints'})).append('API endpoints')
        legend_api = legend_api_wrapper.append(HTMLNode('ul', {'class': 'nav nav-stacked nav-pills subnav'}))

        # Page header
        header = information_wrapper.append(HTMLNode('div', {'class': 'page-header'}))
        header_text = header.append(HTMLNode('h1'))
        header_text.append('{0} API documentation '.format(self.raml.title))
        header_text.append(HTMLNode('small')).append('version {0}'.format(self.raml.version))
        header.append(HTMLNode('p')).append(self.raml.baseUri)

        # Endpoints container
        routes_panel = information_wrapper.append(HTMLNode('div', {'class': 'panel panel-default'}))
        routes_panel.append(HTMLNode('div', {'class': 'panel-heading'})).append(HTMLNode('h3', {'class': 'panel-title', 'id': '_api_endpoints'})).append('API Endpoints')
        routes = routes_panel.append(HTMLNode('div', {'class': 'panel-body'}))

        # The magic happens here.
        for group in self.raml.resources:
            # Create panel for each "group" (first path component)
            panel = routes.append(HTMLNode('div', {'class': 'panel panel-default'}))
            groupc = self.raml.resources[group]
            panel.append(HTMLNode('div', {'class': 'panel-heading'})).append(HTMLNode('h3', {'id': classify(group), 'class': 'panel-title'})).append(group)
            body = panel.append(HTMLNode('div', {'class': 'panel-body'})).append(HTMLNode('div', {'class': 'panel-group'}))
            groupclass = classify(group)

            # Append this to the legend (stacked pills on the right)
            linode = legend_api.append(HTMLNode('li'))
            linode.append(HTMLNode('a', {'href': '#{0}'.format(groupclass)})).append(group)

            # Endpoints
            for ep in collect(groupc, group):
                # Insert each endpoint as a panel into the group panel.
                path = ep._collect_path
                classified = classify(path)
                endpoint_wrapper = body.append(HTMLNode('div', {'class': 'panel panel-white'}))
                endpoint_details = endpoint_wrapper.append(HTMLNode('div', {'class': 'panel-heading'})).append(HTMLNode('h4', {'class': 'panel-title'}))
                endpoint_link = endpoint_details.append(HTMLNode('a', {'class': 'collapsed', 'data-toggle': 'collapse', 'href': '#panel_{0}'.format(classified)}))

                # Path colors happen here.
                parent, child = path.rsplit('/', 1)
                if parent != '':
                    parent = '/{0}'.format(parent.lstrip('/'))
                child = '/{0}'.format(child.lstrip('/'))
                endpoint_link.append(HTMLNode('span', {'class': 'parent'})).append(parent)
                endpoint_link.append(child)

                # Method wrapper (buttons on the right) and the collapsible panel that contains the short descriptions of the methods.
                methods = endpoint_details.append(HTMLNode('span', {'class': 'methods'}))
                details_panel = endpoint_wrapper.append(HTMLNode('div', {'id': 'panel_{0}'.format(classified), 'class': 'panel-collapse collapse'})).append(HTMLNode('div', {'class': 'panel-body'})).append(HTMLNode('div', {'class': 'list-group'}))
                for method in sorted(ep.methods):
                    # Insert each method into a myriad of places
                    methodc = ep.methods[method]
                    method_anchor = '{0}_{1}'.format(classified, method)
                    # Create the method badge
                    badge = methods.append(HTMLNode('a', {'href': '#{0}'.format(method_anchor)})).append(HTMLNode('span', {'class': 'badge badge_{0}'.format(method)}))
                    badge.append('{0} '.format(method))
                    # Append a lock if the endpoint is securedBy anything
                    if methodc.securedBy is not None and len(methodc.securedBy) > 0:
                        badge.append(HTMLNode('span', {'class': 'glyphicon glyphicon-lock', 'title': 'Authentication required'}))

                    methods.append(' ')

                    # Create the method panel. The method panel is an entry in the collapsible list of short descriptions.
                    method_panel = details_panel.append(HTMLNode('div', {'onclick': "window.location.href = '#{0}'".format(method_anchor), 'class': 'list-group-item'}))
                    method_panel.append(badge.copy())
                    method_panel.append(HTMLNode('div', {'class': 'method_description'})).append(HTMLNode('p')).append(methodc.description)
                    method_panel.append(HTMLNode('div', {'class': 'clearfix'}))

                    # Create the method dialog. The method modal is a dialog that shows up if the method badge is clicked anywhere.
                    method_dialog = endpoint_wrapper.append(HTMLNode('div', {'class': 'modal fade', 'tabindex': '0', 'id': method_anchor})).append(HTMLNode('div', {'class': 'modal-dialog'})).append(HTMLNode('div', {'class': 'modal-content'}))

                    # Method dialog header: badge and endpoint
                    dialog_header = method_dialog.append(HTMLNode('div', {'class': 'modal-header'}))
                    dialog_header.append(HTMLNode('button', {'class': 'close', 'data-dismiss': 'modal', 'aria-hidden': 'true'})).append('×')
                    dialog_title = dialog_header.append(HTMLNode('h4', {'class': 'modal-title', 'id': 'myModalLabel'}))
                    dialog_title.append(badge.copy())
                    dialog_title.append(' ')
                    dialog_title.extend(endpoint_link.copy_contents())

                    # Method dialog body: method description, authentication description, request and response details.
                    dialog_body = method_dialog.append(HTMLNode('div', {'class': 'modal-body'}))
                    dialog_body.append(HTMLNode('div', {'class': 'alert alert-info'})).append(HTMLNode('p')).append(methodc.description)

                    # Append a warning box for each security measure on this endpoint.
                    if methodc.securedBy is not None and len(methodc.securedBy) > 0:
                        security_box = dialog_body.append(HTMLNode('div', {'class': 'alert alert-warning'}))
                        if len(methodc.securedBy) > 1:
                            security_box.append(HTMLNode('div', {'class': 'authentication top'})).append(HTMLNode('strong')).append('This endpoint may be used with any of the following authentication schemes:')
                        else:
                            security_box.append(HTMLNode('div', {'class': 'authentication top'})).append(HTMLNode('strong')).append('This endpoint must be used with the following authentication scheme:')
                        for security in methodc.securedBy:
                            if security in self.raml.securitySchemes:
                                mydiv = security_box.append(HTMLNode('div', {'class': 'authentication'}))
                                mydiv.append(HTMLNode('span', {'class': 'glyphicon glyphicon-lock', 'title': 'Authentication required'}))
                                mydiv.append(' Secured by ')
                                mydiv.append(HTMLNode('a', {'href': '#panel__security_{0}'.format(classify(security))})).append(security)
                                mydiv.append(HTMLNode('p')).append(self.raml.securitySchemes[security].description)

                    # Create a tab display where the request and response details will live.
                    tabs = dialog_body.append(HTMLNode('ul', {'class': 'nav nav-tabs'}))
                    tab_contents = dialog_body.append(HTMLNode('div', {'class': 'tab-content'}))
                    first_tab = True

                    # The request tab is only inserted if list of headers, query parameters or a body example is present in the RAML.
                    if (methodc.headers is not None and len(methodc.headers) > 0) or (methodc.queryParameters is not None and len(methodc.queryParameters) > 0) or (methodc.body is not None and len(methodc.body) > 0):
                        first_tab = False
                        tabs.append(HTMLNode('li', {'class': 'active'})).append(HTMLNode('a', {'href': '#{0}_request'.format(method_anchor), 'data-toggle': 'tab'})).append('Request')
                        contents = tab_contents.append(HTMLNode('div', {'class': 'tab-pane active', 'id': '{0}_request'.format(method_anchor)}))

                        # List of headers inserted here.
                        if methodc.headers is not None and len(methodc.headers) > 0:
                            contents.append(HTMLNode('h3')).append('Headers')
                            header_list = contents.append(HTMLNode('ul'))
                            for header in methodc.headers:
                                headerc = methodc.headers[header]
                                header_elem = header_list.append(HTMLNode('li'))
                                if headerc.displayName != "":
                                    header_elem.append(HTMLNode('strong')).append(headerc.displayName)
                                    header_elem.append(': ')
                                    header_elem.append(HTMLNode('em')).append('({0}, {1})'.format(header, 'string' if headerc.type is None else headerc.type))
                                else:
                                    header_elem.append(HTMLNode('strong')).append(header)
                                    header_elem.append(': ')
                                    header_elem.append(HTMLNode('em')).append('({0})'.format('string' if headerc.type is None else headerc.type))
                                header_elem.append(HTMLNode('p')).append(headerc.description)

                        # List of query parameters inserted here
                        if methodc.queryParameters is not None and len(methodc.queryParameters) > 0:
                            contents.append(HTMLNode('h3')).append('Query Parameters')
                            param_list = contents.append(HTMLNode('ul'))
                            for param in methodc.queryParameters:
                                paramc = methodc.queryParameters[param]
                                param_elem = param_list.append(HTMLNode('li'))
                                param_elem.append(HTMLNode('strong')).append(param)
                                param_elem.append(': ')
                                param_elem.append(HTMLNode('em')).append('({0})'.format('string' if paramc.type is None else paramc.type))
                                param_elem.append(HTMLNode('p')).append(paramc.description)

                        if methodc.body is not None and len(methodc.body) > 0:
                            contents.append(HTMLNode('h3')).append('Body')
                            
                            for ctype in methodc.body:
                                ctypec = methodc.body[ctype]
                                example = ctypec.example
                                schema = ctypec.schema
                                contents.append(HTMLNode('p')).append(HTMLNode('strong')).append('Type: {0}'.format(ctype))

                                if schema is not None:
                                    contents.append(HTMLNode('p')).append(HTMLNode('strong')).append('Schema')
                                    param_list = contents.append(HTMLNode('ul'))
                                    for param in schema:
                                        param_name = param_list.append(HTMLNode('li'))
                                        param_name.append(HTMLNode('strong')).append(param)

                                        paramDefinition = dict(schema[param])
                                        paramDesc = 'N/A' if 'description' not in paramDefinition else paramDefinition['description']
                                        paramType = 'string' if 'type' not in paramDefinition else paramDefinition['type']
                                        paramRequired = 'required' if ('required' in paramDefinition) and (paramDefinition['required'] is True) else 'optional'
                                        param_name.append(HTMLNode('p')).append('({0}, {1}): {2}'.format(paramType, paramRequired, paramDesc))
                                        
                                if example is not None:
                                    contents.append(HTMLNode('p')).append(HTMLNode('strong')).append('Example')
                                    contents.append(HTMLNode('pre')).append(HTMLNode('code')).append(json.dumps(example, sort_keys=True, indent=4))


                    # Create the response tab if a response description exists.
                    if methodc.responses is not None and len(methodc.responses) > 0:
                        if first_tab:
                            response_tab = tabs.append(HTMLNode('li', {'class': 'active'}))
                            contents = tab_contents.append(HTMLNode('div', {'class': 'tab-pane active', 'id': '{0}_response'.format(method_anchor)}))
                        else:
                            response_tab = tabs.append(HTMLNode('li'))
                            contents = tab_contents.append(HTMLNode('div', {'class': 'tab-pane', 'id': '{0}_response'.format(method_anchor)}))
                        response_tab.append(HTMLNode('a', {'href': '#{0}_response'.format(method_anchor), 'data-toggle': 'tab'})).append('Response')
                        for code in methodc.responses:
                            # The response details each HTTP status code and the body that is returned for each status code.
                            codec = methodc.responses[code]
                            title = contents.append(HTMLNode('h2'))
                            title.append('HTTP status code ')
                            title.append(HTMLNode('a', {'href': 'http://httpstatus.es/{0}'.format(code), 'target': '_blank', 'rel': 'noreferrer'})).append(code)
                            contents.append(HTMLNode('p')).append(codec.description)
                            if codec.body is not None and len(codec.body) > 0:
                                contents.append(HTMLNode('h3')).append('Body')
                                for ctype in codec.body:
                                    ctypec = codec.body[ctype]
                                    example = ctypec.example
                                    contents.append(HTMLNode('p')).append(HTMLNode('strong')).append('Type: {0}'.format(ctype))
                                    contents.append(HTMLNode('pre')).append(HTMLNode('code')).append(json.dumps(example, sort_keys=True, indent=4))

        if self.raml.securitySchemes is not None and len(self.raml.securitySchemes) > 0:
            legend_security_wrapper = legend.append(HTMLNode('li'))
            legend_security_wrapper.append(HTMLNode('a', {'href': '#_security_schemes'})).append('Security schemes')
            legend_security = legend_security_wrapper.append(HTMLNode('ul', {'class': 'nav nav-stacked nav-pills subnav'}))

            security_panel = information_wrapper.append(HTMLNode('div', {'class': 'panel panel-default'}))
            security_panel.append(HTMLNode('div', {'class': 'panel-heading'})).append(HTMLNode('h3', {'class': 'panel-title', 'id': '_security_schemes'})).append('Security schemes')
            security = security_panel.append(HTMLNode('div', {'class': 'panel-body'}))

            for scheme in self.raml.securitySchemes:
                classified = classify(scheme)
                schemec = self.raml.securitySchemes[scheme]
                legend_security.append(HTMLNode('li')).append(HTMLNode('a', {'href': '#_security_{0}'.format(classified)})).append(scheme)
                elem_wrapper = security.append(HTMLNode('div', {'class': 'panel panel-default'}))
                elem_wrapper.append(HTMLNode('div', {'class': 'panel-heading'})).append(HTMLNode('h3', {'class': 'panel-title', 'id': '_security_{0}'.format(classified)})).append(scheme)
                elem_body = elem_wrapper.append(HTMLNode('div', {'class': 'panel-body'}))
                elem_body.append(HTMLNode('p')).append(schemec.description)
                elem_body.append(HTMLNode('div', {'class': 'right-aligned'})).append(HTMLNode('a', {'href': '#panel__security_{0}'.format(classified)})).append(HTMLNode('span', {'class': 'badge badge_information double'})).append('Information')

                # Modal for the detailed description of the scheme.
                elem_dialog = elem_body.append(HTMLNode('div', {'class': 'modal fade', 'tabindex': '0', 'id': 'panel__security_{0}'.format(classified)})).append(HTMLNode('div', {'class': 'modal-dialog'})).append(HTMLNode('div', {'class': 'modal-content'}))
                dialog_header = elem_dialog.append(HTMLNode('div', {'class': 'modal-header'}))
                dialog_header.append(HTMLNode('button', {'class': 'close', 'data-dismiss': 'modal', 'aria-hidden': 'true'})).append('×')
                dialog_title = dialog_header.append(HTMLNode('h4', {'class': 'modal-title', 'id': 'myModalLabel'}))
                dialog_title.append('Security scheme: {0}'.format(scheme))

                # Method dialog body: method description, authentication description, request and response details.
                dialog_body = elem_dialog.append(HTMLNode('div', {'class': 'modal-body'}))
                dialog_body.append(HTMLNode('div', {'class': 'alert alert-info'})).append(HTMLNode('p')).append(schemec.description)

                if schemec.describedBy is not None:
                    desc = schemec.describedBy
                    tabs = dialog_body.append(HTMLNode('ul', {'class': 'nav nav-tabs'}))
                    tab_contents = dialog_body.append(HTMLNode('div', {'class': 'tab-content'}))
                    first_tab = True

                    # The request tab is only inserted if list of headers, query parameters or a body example is present in the RAML.
                    if (desc.headers is not None and len(desc.headers) > 0) or (desc.queryParameters is not None and len(desc.queryParameters) > 0):
                        first_tab = False
                        tabs.append(HTMLNode('li', {'class': 'active'})).append(HTMLNode('a', {'href': '#_security_{0}_request'.format(classified), 'data-toggle': 'tab'})).append('Request elements')
                        contents = tab_contents.append(HTMLNode('div', {'class': 'tab-pane active', 'id': '_security_{0}_request'.format(classified)}))

                        # List of headers inserted here.
                        if desc.headers is not None and len(desc.headers) > 0:
                            contents.append(HTMLNode('h3')).append('Headers')
                            header_list = contents.append(HTMLNode('ul'))
                            for header in desc.headers:
                                headerc = desc.headers[header]
                                header_elem = header_list.append(HTMLNode('li'))
                                if headerc.displayName != "":
                                    header_elem.append(HTMLNode('strong')).append(headerc.displayName)
                                    header_elem.append(': ')
                                    header_elem.append(HTMLNode('em')).append('({0}, {1})'.format(header, 'string' if headerc.type is None else headerc.type))
                                else:
                                    header_elem.append(HTMLNode('strong')).append(header)
                                    header_elem.append(': ')
                                    header_elem.append(HTMLNode('em')).append('({0})'.format('string' if headerc.type is None else headerc.type))
                                header_elem.append(HTMLNode('p')).append(headerc.description)

                        # List of query parameters inserted here
                        if desc.queryParameters is not None and len(desc.queryParameters) > 0:
                            contents.append(HTMLNode('h3')).append('Query Parameters')
                            param_list = contents.append(HTMLNode('ul'))
                            for param in desc.queryParameters:
                                paramc = desc.queryParameters[param]
                                param_elem = param_list.append(HTMLNode('li'))
                                param_elem.append(HTMLNode('strong')).append(param)
                                param_elem.append(': ')
                                param_elem.append(HTMLNode('em')).append('({0})'.format('string' if paramc.type is None else paramc.type))
                                param_elem.append(HTMLNode('p')).append(paramc.description)

                    # Create the response tab if a response description exists.
                    if desc.responses is not None and len(desc.responses) > 0:
                        if first_tab:
                            response_tab = tabs.append(HTMLNode('li', {'class': 'active'}))
                            contents = tab_contents.append(HTMLNode('div', {'class': 'tab-pane active', 'id': '_security_{0}_response'.format(scheme)}))
                        else:
                            response_tab = tabs.append(HTMLNode('li'))
                            contents = tab_contents.append(HTMLNode('div', {'class': 'tab-pane', 'id': '_security_{0}_response'.format(scheme)}))
                        response_tab.append(HTMLNode('a', {'href': '#_security_{0}_response'.format(scheme), 'data-toggle': 'tab'})).append('Related responses')
                        for code in desc.responses:
                            # The response details each HTTP status code and the body that is returned for each status code.
                            codec = desc.responses[code]
                            title = contents.append(HTMLNode('h2'))
                            title.append('HTTP status code ')
                            title.append(HTMLNode('a', {'href': 'http://httpstatus.es/{0}'.format(code), 'target': '_blank', 'rel': 'noreferrer'})).append(code)
                            contents.append(HTMLNode('p')).append(codec.description)
                            if codec.body is not None and len(codec.body) > 0:
                                contents.append(HTMLNode('h3')).append('Body')
                                for ctype in codec.body:
                                    ctypec = codec.body[ctype]
                                    example = ctypec.example
                                    contents.append(HTMLNode('p')).append(HTMLNode('strong')).append('Type: {0}'.format(ctype))
                                    contents.append(HTMLNode('pre')).append(HTMLNode('code')).append(json.dumps(example, sort_keys=True, indent=4))

        return doc.render(pretty=False, indent=0)
