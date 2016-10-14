import io
import re
import cgi
import random
import inspect
import hashlib
import colorsys

import pygraphviz as pgv

from jinja2  import Template

subgraph_color = '#454545'
default_node_color = '#3f52bf'
path_regex = re.compile(r'site-packages\/(\S+?)\/')


class FrameGraph(object):

    def __init__(self, *args, **kwargs):
        self._graph = pgv.AGraph(*args, **kwargs)

        # Inspired by http://matthiaseisen.com/articles/graphviz/
        self._graph.graph_attr.update({
            'fontsize': '16',
            'fontcolor': 'white',
            'bgcolor': '#333333',
            'rankdir': 'BT'
        })
        self._graph.node_attr.update({
            'fontname': 'Helvetica',
            'shape': 'hexagon',
            'fontcolor': 'white',
            'color': 'white',
            'style': 'filled',
        })
        self._graph.edge_attr.update({
            'style': 'dashed',
            'color': 'white',
            'arrowhead': 'open',
            'fontname': 'Courier',
            'fontsize': '12',
            'fontcolor': 'white',
            'class': 'edge'
        })

        self._subgraphs = {}
        self._num_edges = 0
        self._color_mapping = {}
        self._src_list = []

    def _get_id_from_frame_record(self, frame_record):
        frame, filename, _, name, _, _ = frame_record
        firstlineno = frame.f_code.co_firstlineno
        raw_str = '{0}:{1}:{2}'.format(filename, firstlineno, name)
        return hashlib.sha1(raw_str).hexdigest()

    def _generate_color(self):
        r, g, b = colorsys.hls_to_rgb(random.random(), 0.6, 0.4)
        hex_r = hex(int(r * 255))[2:].zfill(2)
        hex_g = hex(int(g * 255))[2:].zfill(2)
        hex_b = hex(int(b * 255))[2:].zfill(2)
        color = '#{0}{1}{2}'.format(hex_r, hex_g, hex_b)
        return color

    def _get_color_of_subgraph(self, subgraph):
        match = path_regex.search(subgraph)
        if match:
            token = match.group(1)
            if token not in self._color_mapping:
                self._color_mapping[token] = self._generate_color()
            color = self._color_mapping[token]
        else:
            color = default_node_color
        return color

    def add_edge(self, start, end):
        self._num_edges += 1

        self.add_node(start)
        self.add_node(end)

        _, _, lineno, _, _, _ = start

        start_id = self._get_id_from_frame_record(start)
        _, start_filename, _, start_name, _, _ = start
        end_id = self._get_id_from_frame_record(end)
        _, _, _, end_name, _, _ = end

        tooltip='{0} -> {1}'.format(start_name, end_name)
        self._graph.add_edge(
            start_id,
            end_id,
            label='#{0} at {1}'.format(self._num_edges, lineno),
            tooltip=tooltip,
            labeltooltip=tooltip,
            labelURL='javascript:openFile(%r, %d);' % (start_filename, lineno)
        )

    def add_node(self, frame_record):
        frame, filename, _, name, _, _ = frame_record
        firstlineno = frame.f_code.co_firstlineno
        self.add_subgraph(filename)

        node_id = self._get_id_from_frame_record(frame_record)
        if node_id not in self._subgraphs[filename][1]:
            color = self._subgraphs[filename][2]
            label = '{0}:{1}'.format(firstlineno, name)
            self._subgraphs[filename][0].add_node(
                node_id,
                label=label,
                tooltip=label,
                fillcolor=color,
                URL='javascript:openFile(%r, %d);' % (filename, firstlineno),
            )
            self._subgraphs[filename][1].add(node_id)

    def add_subgraph(self, name):
        if name not in self._subgraphs:
            node_color = self._get_color_of_subgraph(name)

            with open(name) as src_file:
                src_str = cgi.escape(src_file.read()).decode('utf-8')
                self._src_list.append((name, src_str))
            
            subgraph = self._graph.add_subgraph(
                name='cluster' + name,
                label=name,
                tooltip=name,
                style='filled',
                color=subgraph_color,
                bgcolor=subgraph_color,
            )
            self._subgraphs[name] = (subgraph, set(), node_color)

    def draw(self, path):
        svg_buf = io.BytesIO()
        self._graph.draw(svg_buf, format='svg', prog='dot' )

        svg_buf.seek(0)
        svg_str = svg_buf.read()
        svg_str = svg_str.replace(
            '<title>%3</title>', '<title></title>')
        html_str = html_template.render(svg=svg_str, src_list=self._src_list)

        with open(path, 'w') as svg_file:
            svg_file.write(html_str.encode('utf-8'))

    def close(self):
        self._graph.close()


def figure_frame(out='figure.html'):
    stack = list(reversed(inspect.stack()))
    graph = FrameGraph(strict=False, directed=True)

    try:
        for index, start in enumerate(stack[:-1]):
            end = stack[index + 1]
            graph.add_edge(start, end)

        if out:
            graph.draw(out)
            graph.close()
    finally:
        del stack, graph

html_template = Template(u'<!DOCTYPE html>\n<html lang="zh">\n<head>\n  <meta charset="UTF-8">\n  <title>Frame Figure</title>\n  <style>\n    /* prism.css */\n\n    /* http://prismjs.com/download.html?themes=prism-okaidia&languages=python&plugins=line-highlight+line-numbers */\n    /**\n     * okaidia theme for JavaScript, CSS and HTML\n     * Loosely based on Monokai textmate theme by http://www.monokai.nl/\n     * @author ocodia\n     */\n\n    code[class*="language-"],\n    pre[class*="language-"] {\n        color: #f8f8f2;\n        background: none;\n        text-shadow: 0 1px rgba(0, 0, 0, 0.3);\n        font-family: Consolas, Monaco, \'Andale Mono\', \'Ubuntu Mono\', monospace;\n        text-align: left;\n        white-space: pre;\n        word-spacing: normal;\n        word-break: normal;\n        word-wrap: normal;\n        line-height: 1.5;\n\n        -moz-tab-size: 4;\n        -o-tab-size: 4;\n        tab-size: 4;\n\n        -webkit-hyphens: none;\n        -moz-hyphens: none;\n        -ms-hyphens: none;\n        hyphens: none;\n    }\n\n    /* Code blocks */\n    pre[class*="language-"] {\n        padding: 1em;\n        margin: .5em 0;\n        overflow: auto;\n        border-radius: 0.3em;\n    }\n\n    :not(pre) > code[class*="language-"],\n    pre[class*="language-"] {\n        background: #272822;\n    }\n\n    /* Inline code */\n    :not(pre) > code[class*="language-"] {\n        padding: .1em;\n        border-radius: .3em;\n        white-space: normal;\n    }\n\n    .token.comment,\n    .token.prolog,\n    .token.doctype,\n    .token.cdata {\n        color: slategray;\n    }\n\n    .token.punctuation {\n        color: #f8f8f2;\n    }\n\n    .namespace {\n        opacity: .7;\n    }\n\n    .token.property,\n    .token.tag,\n    .token.constant,\n    .token.symbol,\n    .token.deleted {\n        color: #f92672;\n    }\n\n    .token.boolean,\n    .token.number {\n        color: #ae81ff;\n    }\n\n    .token.selector,\n    .token.attr-name,\n    .token.string,\n    .token.char,\n    .token.builtin,\n    .token.inserted {\n        color: #a6e22e;\n    }\n\n    .token.operator,\n    .token.entity,\n    .token.url,\n    .language-css .token.string,\n    .style .token.string,\n    .token.variable {\n        color: #f8f8f2;\n    }\n\n    .token.atrule,\n    .token.attr-value,\n    .token.function {\n        color: #e6db74;\n    }\n\n    .token.keyword {\n        color: #66d9ef;\n    }\n\n    .token.regex,\n    .token.important {\n        color: #fd971f;\n    }\n\n    .token.important,\n    .token.bold {\n        font-weight: bold;\n    }\n    .token.italic {\n        font-style: italic;\n    }\n\n    .token.entity {\n        cursor: help;\n    }\n\n    pre[data-line] {\n        position: relative;\n        padding: 1em 0 1em 3em;\n    }\n\n    .line-highlight {\n        position: absolute;\n        left: 0;\n        right: 0;\n        padding: inherit 0;\n        margin-top: 1em; /* Same as .prism\xe2\x80\x99s padding-top */\n\n        background: hsla(24, 20%, 50%,.08);\n        background: linear-gradient(to right, hsla(24, 20%, 50%,.1) 70%, hsla(24, 20%, 50%,0));\n\n        pointer-events: none;\n\n        line-height: inherit;\n        white-space: pre;\n    }\n\n        .line-highlight:before,\n        .line-highlight[data-end]:after {\n            content: attr(data-start);\n            position: absolute;\n            top: .4em;\n            left: .6em;\n            min-width: 1em;\n            padding: 0 .5em;\n            background-color: hsla(24, 20%, 50%,.4);\n            color: hsl(24, 20%, 95%);\n            font: bold 65%/1.5 sans-serif;\n            text-align: center;\n            vertical-align: .3em;\n            border-radius: 999px;\n            text-shadow: none;\n            box-shadow: 0 1px white;\n        }\n\n        .line-highlight[data-end]:after {\n            content: attr(data-end);\n            top: auto;\n            bottom: .4em;\n        }\n\n    pre.line-numbers {\n        position: relative;\n        padding-left: 3.8em;\n        counter-reset: linenumber;\n    }\n\n    pre.line-numbers > code {\n        position: relative;\n    }\n\n    .line-numbers .line-numbers-rows {\n        position: absolute;\n        pointer-events: none;\n        top: 0;\n        font-size: 100%;\n        left: -3.8em;\n        width: 3em; /* works for line-numbers below 1000 lines */\n        letter-spacing: -1px;\n        border-right: 1px solid #999;\n\n        -webkit-user-select: none;\n        -moz-user-select: none;\n        -ms-user-select: none;\n        user-select: none;\n\n    }\n\n    .line-numbers-rows > span {\n        pointer-events: none;\n        display: block;\n        counter-increment: linenumber;\n    }\n\n    .line-numbers-rows > span:before {\n        content: counter(linenumber);\n        color: #999;\n        display: block;\n        padding-right: 0.8em;\n        text-align: right;\n    }\n\n    /* end of prism.css */\n    body {\n      margin: 0;\n      background-color: #333333;\n    }\n\n    .container .edge {\n      cursor: pointer;\n    }\n\n    .container .edge:hover > g {\n      stroke-width: 3px;\n    }\n\n    .modal-content {\n      position: fixed;\n      z-index: 100;\n      top: 50px;\n      left: 100px;\n      right: 100px;\n      bottom: 100px;\n      background-color: #fff;\n      box-shadow: 0 20px 80px rgba(0,0,0,.3);\n      opacity: 0;\n      visibility: hidden;\n      transform: translateY(-100px);\n      transition: all .6s cubic-bezier(0.175, 0.885, 0.32, 1.275);\n    }\n\n    .modal.show .modal-content {\n      opacity: 1;\n      visibility: visible;\n      transform: translateY(0);\n      overflow: hidden;\n    }\n\n    .modal .modal-backdrop {\n      position: absolute;\n      z-index: 99;\n      top: 0;\n      left: 0;\n      right: 0;\n      bottom: 0;\n      background-color: rgba(0,0,0,.1);\n      opacity: 0;\n      transition: all .6s;\n      visibility: hidden;\n    }\n\n    .modal.show .modal-backdrop {\n      visibility: visible;\n      opacity: 1;\n    }\n\n    .modal .modal-content #source-code-editor {\n      position: relative;\n      width: 100%;\n      height: 100%;\n      font-size: 18px;\n      background-color: #272822;\n      overflow: auto;\n    }\n\n    .modal .modal-content .line-highlight {\n      margin-top: .9em;\n      background: linear-gradient(to right, hsla(199, 20%, 50%, 0.32) 70%, hsla(24, 20%, 50%,0));\n    }\n\n    .line-numbers .line-numbers-rows {\n      top: -3px;\n    }\n  </style>\n  <script>\n    function openFile () {}\n  </script>\n</head>\n<body>\n<div class="container">\n  <div id="svg-wrapper">\n    {{ svg }}\n  </div>\n</div>\n{% for src in src_list %}\n<script type="text/plain" data-source="{{ src[0] }}">{{ src[1] }}</script>\n{% endfor %}\n<script type="text/javascript">\n/* http://prismjs.com/download.html?themes=prism-okaidia&languages=python&plugins=line-highlight+line-numbers */\nvar _self="undefined"!=typeof window?window:"undefined"!=typeof WorkerGlobalScope&&self instanceof WorkerGlobalScope?self:{},Prism=function(){var e=/\\blang(?:uage)?-(\\w+)\\b/i,t=0,n=_self.Prism={util:{encode:function(e){return e instanceof a?new a(e.type,n.util.encode(e.content),e.alias):"Array"===n.util.type(e)?e.map(n.util.encode):e.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/\\u00a0/g," ")},type:function(e){return Object.prototype.toString.call(e).match(/\\[object (\\w+)\\]/)[1]},objId:function(e){return e.__id||Object.defineProperty(e,"__id",{value:++t}),e.__id},clone:function(e){var t=n.util.type(e);switch(t){case"Object":var a={};for(var r in e)e.hasOwnProperty(r)&&(a[r]=n.util.clone(e[r]));return a;case"Array":return e.map&&e.map(function(e){return n.util.clone(e)})}return e}},languages:{extend:function(e,t){var a=n.util.clone(n.languages[e]);for(var r in t)a[r]=t[r];return a},insertBefore:function(e,t,a,r){r=r||n.languages;var i=r[e];if(2==arguments.length){a=arguments[1];for(var l in a)a.hasOwnProperty(l)&&(i[l]=a[l]);return i}var o={};for(var s in i)if(i.hasOwnProperty(s)){if(s==t)for(var l in a)a.hasOwnProperty(l)&&(o[l]=a[l]);o[s]=i[s]}return n.languages.DFS(n.languages,function(t,n){n===r[e]&&t!=e&&(this[t]=o)}),r[e]=o},DFS:function(e,t,a,r){r=r||{};for(var i in e)e.hasOwnProperty(i)&&(t.call(e,i,e[i],a||i),"Object"!==n.util.type(e[i])||r[n.util.objId(e[i])]?"Array"!==n.util.type(e[i])||r[n.util.objId(e[i])]||(r[n.util.objId(e[i])]=!0,n.languages.DFS(e[i],t,i,r)):(r[n.util.objId(e[i])]=!0,n.languages.DFS(e[i],t,null,r)))}},plugins:{},highlightAll:function(e,t){var a={callback:t,selector:\'code[class*="language-"], [class*="language-"] code, code[class*="lang-"], [class*="lang-"] code\'};n.hooks.run("before-highlightall",a);for(var r,i=a.elements||document.querySelectorAll(a.selector),l=0;r=i[l++];)n.highlightElement(r,e===!0,a.callback)},highlightElement:function(t,a,r){for(var i,l,o=t;o&&!e.test(o.className);)o=o.parentNode;o&&(i=(o.className.match(e)||[,""])[1].toLowerCase(),l=n.languages[i]),t.className=t.className.replace(e,"").replace(/\\s+/g," ")+" language-"+i,o=t.parentNode,/pre/i.test(o.nodeName)&&(o.className=o.className.replace(e,"").replace(/\\s+/g," ")+" language-"+i);var s=t.textContent,u={element:t,language:i,grammar:l,code:s};if(n.hooks.run("before-sanity-check",u),!u.code||!u.grammar)return n.hooks.run("complete",u),void 0;if(n.hooks.run("before-highlight",u),a&&_self.Worker){var c=new Worker(n.filename);c.onmessage=function(e){u.highlightedCode=e.data,n.hooks.run("before-insert",u),u.element.innerHTML=u.highlightedCode,r&&r.call(u.element),n.hooks.run("after-highlight",u),n.hooks.run("complete",u)},c.postMessage(JSON.stringify({language:u.language,code:u.code,immediateClose:!0}))}else u.highlightedCode=n.highlight(u.code,u.grammar,u.language),n.hooks.run("before-insert",u),u.element.innerHTML=u.highlightedCode,r&&r.call(t),n.hooks.run("after-highlight",u),n.hooks.run("complete",u)},highlight:function(e,t,r){var i=n.tokenize(e,t);return a.stringify(n.util.encode(i),r)},tokenize:function(e,t){var a=n.Token,r=[e],i=t.rest;if(i){for(var l in i)t[l]=i[l];delete t.rest}e:for(var l in t)if(t.hasOwnProperty(l)&&t[l]){var o=t[l];o="Array"===n.util.type(o)?o:[o];for(var s=0;s<o.length;++s){var u=o[s],c=u.inside,g=!!u.lookbehind,h=!!u.greedy,f=0,d=u.alias;if(h&&!u.pattern.global){var p=u.pattern.toString().match(/[imuy]*$/)[0];u.pattern=RegExp(u.pattern.source,p+"g")}u=u.pattern||u;for(var m=0,y=0;m<r.length;y+=(r[m].matchedStr||r[m]).length,++m){var v=r[m];if(r.length>e.length)break e;if(!(v instanceof a)){u.lastIndex=0;var b=u.exec(v),k=1;if(!b&&h&&m!=r.length-1){if(u.lastIndex=y,b=u.exec(e),!b)break;for(var w=b.index+(g?b[1].length:0),_=b.index+b[0].length,A=m,S=y,P=r.length;P>A&&_>S;++A)S+=(r[A].matchedStr||r[A]).length,w>=S&&(++m,y=S);if(r[m]instanceof a||r[A-1].greedy)continue;k=A-m,v=e.slice(y,S),b.index-=y}if(b){g&&(f=b[1].length);var w=b.index+f,b=b[0].slice(f),_=w+b.length,x=v.slice(0,w),O=v.slice(_),j=[m,k];x&&j.push(x);var N=new a(l,c?n.tokenize(b,c):b,d,b,h);j.push(N),O&&j.push(O),Array.prototype.splice.apply(r,j)}}}}}return r},hooks:{all:{},add:function(e,t){var a=n.hooks.all;a[e]=a[e]||[],a[e].push(t)},run:function(e,t){var a=n.hooks.all[e];if(a&&a.length)for(var r,i=0;r=a[i++];)r(t)}}},a=n.Token=function(e,t,n,a,r){this.type=e,this.content=t,this.alias=n,this.matchedStr=a||null,this.greedy=!!r};if(a.stringify=function(e,t,r){if("string"==typeof e)return e;if("Array"===n.util.type(e))return e.map(function(n){return a.stringify(n,t,e)}).join("");var i={type:e.type,content:a.stringify(e.content,t,r),tag:"span",classes:["token",e.type],attributes:{},language:t,parent:r};if("comment"==i.type&&(i.attributes.spellcheck="true"),e.alias){var l="Array"===n.util.type(e.alias)?e.alias:[e.alias];Array.prototype.push.apply(i.classes,l)}n.hooks.run("wrap",i);var o="";for(var s in i.attributes)o+=(o?" ":"")+s+\'="\'+(i.attributes[s]||"")+\'"\';return"<"+i.tag+\' class="\'+i.classes.join(" ")+\'"\'+(o?" "+o:"")+">"+i.content+"</"+i.tag+">"},!_self.document)return _self.addEventListener?(_self.addEventListener("message",function(e){var t=JSON.parse(e.data),a=t.language,r=t.code,i=t.immediateClose;_self.postMessage(n.highlight(r,n.languages[a],a)),i&&_self.close()},!1),_self.Prism):_self.Prism;var r=document.currentScript||[].slice.call(document.getElementsByTagName("script")).pop();return r&&(n.filename=r.src,document.addEventListener&&!r.hasAttribute("data-manual")&&("loading"!==document.readyState?window.requestAnimationFrame?window.requestAnimationFrame(n.highlightAll):window.setTimeout(n.highlightAll,16):document.addEventListener("DOMContentLoaded",n.highlightAll))),_self.Prism}();"undefined"!=typeof module&&module.exports&&(module.exports=Prism),"undefined"!=typeof global&&(global.Prism=Prism);\nPrism.languages.python={"triple-quoted-string":{pattern:/"""[\\s\\S]+?"""|\'\'\'[\\s\\S]+?\'\'\'/,alias:"string"},comment:{pattern:/(^|[^\\\\])#.*/,lookbehind:!0},string:{pattern:/("|\')(?:\\\\\\\\|\\\\?[^\\\\\\r\\n])*?\\1/,greedy:!0},"function":{pattern:/((?:^|\\s)def[ \\t]+)[a-zA-Z_][a-zA-Z0-9_]*(?=\\()/g,lookbehind:!0},"class-name":{pattern:/(\\bclass\\s+)[a-z0-9_]+/i,lookbehind:!0},keyword:/\\b(?:as|assert|async|await|break|class|continue|def|del|elif|else|except|exec|finally|for|from|global|if|import|in|is|lambda|pass|print|raise|return|try|while|with|yield)\\b/,"boolean":/\\b(?:True|False)\\b/,number:/\\b-?(?:0[bo])?(?:(?:\\d|0x[\\da-f])[\\da-f]*\\.?\\d*|\\.\\d+)(?:e[+-]?\\d+)?j?\\b/i,operator:/[-+%=]=?|!=|\\*\\*?=?|\\/\\/?=?|<[<=>]?|>[=>]?|[&|^~]|\\b(?:or|and|not)\\b/,punctuation:/[{}[\\];(),.:]/};\n!function(){function e(e,t){return Array.prototype.slice.call((t||document).querySelectorAll(e))}function t(e,t){return t=" "+t+" ",(" "+e.className+" ").replace(/[\\n\\t]/g," ").indexOf(t)>-1}function n(e,n,i){for(var o,a=n.replace(/\\s+/g,"").split(","),l=+e.getAttribute("data-line-offset")||0,d=r()?parseInt:parseFloat,c=d(getComputedStyle(e).lineHeight),s=0;o=a[s++];){o=o.split("-");var u=+o[0],m=+o[1]||u,h=document.createElement("div");h.textContent=Array(m-u+2).join(" \\n"),h.setAttribute("aria-hidden","true"),h.className=(i||"")+" line-highlight",t(e,"line-numbers")||(h.setAttribute("data-start",u),m>u&&h.setAttribute("data-end",m)),h.style.top=(u-l-1)*c+"px",t(e,"line-numbers")?e.appendChild(h):(e.querySelector("code")||e).appendChild(h)}}function i(){var t=location.hash.slice(1);e(".temporary.line-highlight").forEach(function(e){e.parentNode.removeChild(e)});var i=(t.match(/\\.([\\d,-]+)$/)||[,""])[1];if(i&&!document.getElementById(t)){var r=t.slice(0,t.lastIndexOf(".")),o=document.getElementById(r);o&&(o.hasAttribute("data-line")||o.setAttribute("data-line",""),n(o,i,"temporary "),document.querySelector(".temporary.line-highlight").scrollIntoView())}}if("undefined"!=typeof self&&self.Prism&&self.document&&document.querySelector){var r=function(){var e;return function(){if("undefined"==typeof e){var t=document.createElement("div");t.style.fontSize="13px",t.style.lineHeight="1.5",t.style.padding=0,t.style.border=0,t.innerHTML="&nbsp;<br />&nbsp;",document.body.appendChild(t),e=38===t.offsetHeight,document.body.removeChild(t)}return e}}(),o=0;Prism.hooks.add("complete",function(t){var r=t.element.parentNode,a=r&&r.getAttribute("data-line");r&&a&&/pre/i.test(r.nodeName)&&(clearTimeout(o),e(".line-highlight",r).forEach(function(e){e.parentNode.removeChild(e)}),n(r,a),o=setTimeout(i,1))}),window.addEventListener&&window.addEventListener("hashchange",i)}}();\n!function(){"undefined"!=typeof self&&self.Prism&&self.document&&Prism.hooks.add("complete",function(e){if(e.code){var t=e.element.parentNode,s=/\\s*\\bline-numbers\\b\\s*/;if(t&&/pre/i.test(t.nodeName)&&(s.test(t.className)||s.test(e.element.className))&&!e.element.querySelector(".line-numbers-rows")){s.test(e.element.className)&&(e.element.className=e.element.className.replace(s,"")),s.test(t.className)||(t.className+=" line-numbers");var n,a=e.code.match(/\\n(?!$)/g),l=a?a.length+1:1,r=new Array(l+1);r=r.join("<span></span>"),n=document.createElement("span"),n.setAttribute("aria-hidden","true"),n.className="line-numbers-rows",n.innerHTML=r,t.hasAttribute("data-start")&&(t.style.counterReset="linenumber "+(parseInt(t.getAttribute("data-start"),10)-1)),e.element.appendChild(n)}}})}();\n</script>\n<script type="text/javascript">\n/**\n * Thanks for the contribution made by PeachScript <https://github.com/PeachScript>!\n */\n\n/**\n * enable zoom feature for some element\n * @param {DOM}    elm  target element\n * @param {Number} step zoom step, default: 0.1\n * @param {Number} max  maximum zoom value\n * @param {Number} min  minimum zoom value, default: 0\n */\nfunction enableZoomForElm(elm, step, max, min) {\n  var prefixs = [\'webkitTransform\', \'mozTransform\', \'msTransform\', \'oTransform\', \'transform\'];\n  step = step || .1;\n\n  prefixs.forEach(function (item) {\n    elm.style[item + \'Origin\'] = \'top left\';\n  });\n\n  function getScale () {\n    var styles = getComputedStyle(elm);\n    var scale = parseFloat((styles.transform.match(/matrix\\((-?\\d*\\.?\\d+),\\s*0,\\s*0,\\s*(-?\\d*\\.?\\d+),\\s*0,\\s*0\\)/) || [])[1]);\n    return isNaN(scale) ? 1 : scale;\n  }\n\n  function setScale (target) {\n    prefixs.forEach(function (item) {\n      var current = elm.style[item] || \'\';\n      var scale = parseFloat((current.match(/scale\\((\\d.?\\d?)\\)/) || [])[1]);\n\n      if (isNaN(scale)) {\n        elm.style[item] = \'scale(\' + target + \')\';\n      } else {\n        elm.style[item] = current.replace(/scale\\(\\d.?\\d?\\)/, \'scale(\' + target + \')\');\n      }\n    });\n  }\n\n  return {\n    zoomIn: function () {\n      var target = getScale() + step;\n      if (max === undefined || target < max) {\n        setScale(target);\n      }\n      return this;\n    },\n    zoomOut: function () {\n      var target = getScale() - step;\n      if (target > (min || 0)) {\n        setScale(target);\n      }\n      return this;\n    },\n    setScale: function (target) {\n      setScale(target);\n      return this;\n    },\n    resetScale: function () {\n      setScale(1);\n      return this;\n    }\n  };\n}\n\n/**\n * hot key bind function\n * @param  {String}   key target key name\n * @param  {Function} cb  callback\n * @param  {DOM}      elm the element which be used listen keydown event\n */\nfunction hotKeyBind (key, cb, elm) {\n  var keyMapping = {\n    \'0\': 48,\n    \'z\': 90,\n    \'x\': 88,\n    \'esc\': 27\n  };\n  (elm || window).addEventListener(\'keydown\', function (ev) {\n    if ((ev || event).keyCode === keyMapping[key]) {\n      cb();\n    }\n  });\n}\n\n/**\n * Modal Class\n * @return {Object} Modal Instance\n */\nfunction Modal () {\n  var container = document.createElement(\'div\');\n  var content = document.createElement(\'div\');\n  var backdrop = document.createElement(\'div\');\n\n  container.setAttribute(\'modal-id\', new Date().getTime());\n  container.classList.add(\'modal\');\n  content.classList.add(\'modal-content\');\n  backdrop.classList.add(\'modal-backdrop\');\n\n  container.appendChild(content);\n  container.appendChild(backdrop);\n  document.body.appendChild(container);\n\n  backdrop.addEventListener(\'click\', function () {\n    container.classList.remove(\'show\');\n  });\n\n  return {\n    show: function () {\n      container.classList.add(\'show\');\n      return this;\n    },\n    hide: function () {\n      container.classList.remove(\'show\');\n      return this;\n    },\n    setContent: function (html) {\n      content.innerHTML = html;\n      return this;\n    }\n  };\n}\n\nvar zoomHandler = new enableZoomForElm(document.getElementById(\'svg-wrapper\'));\nhotKeyBind(\'x\', zoomHandler.zoomIn);\nhotKeyBind(\'z\', zoomHandler.zoomOut);\nhotKeyBind(\'0\', zoomHandler.resetScale);\n\nvar modal = new Modal;\nmodal.setContent(\'<div id="source-code-editor"><pre class="line-numbers"><code class="language-python"></code></pre></div>\');\nhotKeyBind(\'esc\', modal.hide);\n\nvar sourceCodeContainer = document.getElementById(\'source-code-editor\');\n\n// Disable double scroll for outer element\nsourceCodeContainer.addEventListener(\'mousewheel\', function (ev) {\n  var elm = ev.currentTarget;\n  var scrollTop = elm.scrollTop;\n  var scrollHeight = elm.scrollHeight;\n  var height = elm.clientHeight;\n  var event = ev.originalEvent || ev;\n\n  var delta = (event.wheelDelta) ? event.wheelDelta : -(event.detail || 0);\n\n  if ((delta > 0 && scrollTop <= delta) ||\n      (delta < 0 && scrollHeight - height - scrollTop <= -1 * delta)) {\n    elm.scrollTop = delta > 0 ? 0 : scrollHeight;\n    event.preventDefault();\n  }\n});\n\nvar sourceCode = (function () {\n  var all = document.getElementsByTagName(\'script\');\n  var result = {};\n  Array.prototype.forEach.call(all, function (item) {\n    if (item.hasAttribute(\'data-source\')) {\n      result[item.getAttribute(\'data-source\')] = item;\n    }\n  });\n\n  return result;\n})();\n\n/**\n * open file function\n * @param  {String} url  source code file url\n * @param  {Number} line line number\n */\nfunction openFile (url, line) {\n  sourceCodeContainer.getElementsByTagName(\'pre\')[0]\n                     .setAttribute(\'data-line\', line);\n  sourceCodeContainer.getElementsByTagName(\'code\')[0].innerHTML = sourceCode[url].innerHTML;\n  Prism.highlightAll();\n  modal.show();\n  sourceCodeContainer.scrollTop = parseInt(document.getElementsByClassName(\'line-highlight\')[0].style.top) - 100;\n}\n</script>\n</body>\n</html>\n')