import os
import re
from lxml.etree import XPath
import html
import lxml.etree as ET
from py_asciimath.translator.translator import ASCIIMath2Tex

cur_file = os.path.abspath(__file__)
xsl_path = os.path.join(os.path.dirname(cur_file), "mmltex/mmltex.xsl")

xslt = ET.parse(xsl_path, parser=None)
transform = ET.XSLT(xslt)     

color_regex = re.compile(r"\\textcolor\[.*?\]\{.*?\}")

latex_image_class_names = [
    "latexcenter",
    "latex",
    "tex",
    "latexdisplay",
    "latexblock",
    "latexblockcenter",
]

asciimath2tex = ASCIIMath2Tex(log=False)
def extract_asciimath(s):
    parsed = asciimath2tex.translate(s)
    return parsed

def html_unescape(s):
    return html.unescape(s)

def get_class_xpath(class_name):
    return f"//*[contains(concat(' ', @class, ' '), ' {class_name} ')]"

def mml_to_latex(mml_code):
    # Remove any attibutes from the math tag
    # Attention: replace into [itex] in the begining
    mml_code = mml_code.replace("[itex]", "<math>").replace("[/itex]", "</math>")
    mml_code = re.sub(r"(<math.*?>)", r"\1", mml_code)
    mml_ns = mml_code.replace(
        "<math>", '<math xmlns="http://www.w3.org/1998/Math/MathML">'
    )  # Required.
    mml_dom = ET.fromstring(mml_ns, parser=None)
    mmldom = transform(mml_dom)
    latex_code = str(mmldom)
    return latex_code

def wrap_math(s, display=False):
    s = re.sub(r"\s+", " ", s)
    s = color_regex.sub("", s)
    s = s.replace("$", "")
    s = s.replace("\n", " ")
    s = s.strip()
    if len(s) == 0:
        return s
    if display:
        return "$$" + s + "$$"
    return "$" + s + "$"

_hexdig = '0123456789ABCDEFabcdef'
_hextobyte = None

def unquote_to_bytes(string):
    """unquote_to_bytes('abc%20def') -> b'abc def'."""
    # Note: strings are encoded as UTF-8. This is only an issue if it contains
    # unescaped non-ASCII characters, which URIs should not.
    if not string:
        # Is it a string-like object?
        string.split
        return b''
    if isinstance(string, str):
        string = string.encode('utf-8')
    bits = string.split(b'%')
    if len(bits) == 1:
        return string
    res = [bits[0]]
    append = res.append
    # Delay the initialization of the table to not waste memory
    # if the function is never called
    global _hextobyte
    if _hextobyte is None:
        _hextobyte = {(a + b).encode(): bytes.fromhex(a + b)
                      for a in _hexdig for b in _hexdig}
    for item in bits[1:]:
        try:
            append(_hextobyte[item[:2]])
            append(item[2:])
        except KeyError:
            append(b'%')
            append(item)
    return b''.join(res)

_asciire = re.compile('([\x00-\x7f]+)')

def unquote(string, encoding='utf-8', errors='replace'):
    """Replace %xx escapes by their single-character equivalent. The optional
    encoding and errors parameters specify how to decode percent-encoded
    sequences into Unicode characters, as accepted by the bytes.decode()
    method.
    By default, percent-encoded sequences are decoded with UTF-8, and invalid
    sequences are replaced by a placeholder character.

    unquote('abc%20def') -> 'abc def'.
    """
    if isinstance(string, bytes):
        return unquote_to_bytes(string).decode(encoding, errors)
    if '%' not in string:
        string.split
        return string
    if encoding is None:
        encoding = 'utf-8'
    if errors is None:
        errors = 'replace'
    bits = _asciire.split(string)
    res = [bits[0]]
    append = res.append
    for i in range(1, len(bits), 2):
        append(unquote_to_bytes(bits[i]).decode(encoding, errors))
        append(bits[i + 1])
    return ''.join(res)

def convert_math_node(tree):
    '''convert math node to latex format'''
    
    for texerror in tree.xpath(get_class_xpath('texerror')):
        match = re.search(r"\{(.{1,})\}", texerror.text)
        if match:
            texerror.text = wrap_math(match.group(1))
    
    for img in tree.xpath('//img'):
        class_attr = img.get("class")
        if class_attr is not None:
            class_list = class_attr.split(" ")   
            if any([img_class in class_list for img_class in latex_image_class_names]):
                alt = img.get("alt")
                if alt is not None:
                    new_span = ET.Element("span", attrib=None, nsmap=None)
                    new_span.text = wrap_math(alt)
                    parent = img.getparent()
                    parent.replace(img, new_span)
        
        src = img.getattr("src")
        if src is None:
            continue
        
        if "codecogs.com" in src:
            try:
                latex = src.split("?")[1:]
                latex = "?".join(latex)  # In case there are multiple ? in the latex
                latex = unquote(latex)
                new_span = ET.Element("span", attrib=None, nsmap=None)
                new_span.text = wrap_math(latex)
                parent = img.getparent()
                parent.replace(img, new_span)
            except:
                pass          
        if "latex.php" in src:
            try:
                alt = img.get("alt")
                if alt is None:
                    continue
                alt = unquote(alt)
                new_span = ET.Element("span", attrib=None, nsmap=None)
                new_span.text = wrap_math(alt)
                parent = img.getparent()
                parent.replace(img, new_span)
            except:
                pass  
        if "/images/math/codecogs" in src:
            try:
                alt = img.get("alt")
                if alt is None:
                    continue
                alt = unquote(alt)
                new_span = ET.Element("span", attrib=None, nsmap=None)
                new_span.text = wrap_math(alt)
                parent = img.getparent()
                parent.replace(img, new_span)
            except:
                pass
        if "mimetex.cgi" in src:
            try:
                latex = src.split("?")[1:]
                latex = "?".join(latex)  # In case there are multiple ? in the latex
                latex = unquote(latex)
                new_span = ET.Element("span", attrib=None, nsmap=None)
                new_span.text = wrap_math(latex)
                parent = img.getparent()
                parent.replace(img, new_span)
            except:
                pass
        if "mathtex.cgi" in src:
            try:
                latex = src.split("?")[1:]
                latex = "?".join(latex)  # In case there are multiple ? in the latex
                latex = unquote(latex)
                new_span = ET.Element("span", attrib=None, nsmap=None)
                new_span.text = wrap_math(alt)
                parent = img.getparent()
                parent.replace(img, new_span)
            except:
                pass
        for latex_signal in ["tex?", "?latex=", "?tex="]:
            if latex_signal in src:
                try:
                    latex = src.split("latex_signal", 1)[1]
                    latex = unquote(latex)
                    new_span = ET.Element("span", attrib=None, nsmap=None)
                    new_span.text = wrap_math(alt)
                    parent = img.getparent()
                    parent.replace(img, new_span)
                except:
                    pass
        for latex_signal in ["tex", "latex"]:
            try:
                # they usually have "alt='-i u_t + &#92;Delta u = |u|^2 u'"
                alt = img.getattr(latex_signal)
                if alt is None:
                    continue
                # Unescape the latex
                alt = unquote(alt)
                # Get the latex
                new_span = ET.Element("span", attrib=None, nsmap=None)
                new_span.text = wrap_math(alt)
                parent = img.getparent()
                parent.replace(img, new_span)
            except:
                pass
        
        class_attr = img.get("class")
        if class_attr is not None and "x-ck12" in class_attr:
            try:
                alt = img.get("alt")
                if alt is None:
                    continue
                latex = unquote(alt)
                new_span = ET.Element("span", attrib=None, nsmap=None)
                new_span.text = wrap_math(alt)
                parent = img.getparent()
                parent.replace(img, new_span)
            except:
                pass
        
    for math_container_node in tree.xpath(get_class_xpath('math-container')):
        text = math_container_node.text
        new_span = ET.Element("span", attrib=None, nsmap=None)
        new_span.text = wrap_math(text)
        parent = math_container_node.getparent()
        parent.replace(math_container_node, new_span)
    
    for katex_node in tree.xpath(get_class_xpath('wp-katex-eq')):
        text = katex_node.text
        new_span = ET.Element("span", attrib=None, nsmap=None)
        display_attr = katex_node.get("data-display")
        if display_attr is not None:
            display = display_attr == "true"
        else:
            display = False
        new_span.text = wrap_math(text, display=display)
        parent = katex_node.getparent()
        parent.replace(katex_node, new_span)
        
    for script_tag in tree.xpath('//script[@type="math/tex"]'):
        text = script_tag.text
        new_span = ET.Element("span", attrib=None, nsmap=None)
        display = "display" in script_tag.get("type")
        new_span.text = wrap_math(text, display=display)
        parent = script_tag.getparent()
        parent.replace(script_tag, new_span)
        mathjax_id = script_tag.get("id")
        if mathjax_id:
            mathjax_id = "-".join(mathjax_id.split("-")[:3])
            for unused_tag in parent.xpath(f'.//*[contains(@id, "{mathjax_id}")]'):
                unused_tag_parent = unused_tag.getparent()
                unused_tag_parent.remove(unused_tag)
    
    for script_tag in tree.xpath('//script[@type="math/asciimath"]'):
        try:
            text = script_tag.text
            new_span = ET.Element("span", attrib=None, nsmap=None)
            wrapped_asciimath = wrap_math(extract_asciimath(text))
            new_span.text = wrapped_asciimath
            parent = script_tag.getparent()
            parent.replace(script_tag, new_span)
        except:
            # Delete this script tag
            parent = script_tag.getparent()
            parent.remove(script_tag)
    
    for script_tag in tree.xpath('//script[contains(@type, "math/mml")]'):
        try:
            # Try translating to LaTeX
            mathml = script_tag.text
            mathml = html_unescape(mathml)
            # If this includes xmlns:mml, then we need to replace all
            # instances of mml: with nothing
            if "xmlns:mml" in mathml:
                mathml = mathml.replace("mml:", "")
                # replace xmlns:mml="..." with nothing
                mathml = re.sub(r'xmlns:mml=".*?"', "", mathml) 
            latex = mml_to_latex(mathml)
            # Make a new span tag
            new_span = ET.Element("span", attrib=None, nsmap=None)
            # Set the html of the new span tag to the text
            wrapped_latex = wrap_math(latex)
            new_span.text = wrapped_latex
            # Then, we need to replace the math tag with the new span tag
            parent = script_tag.getparent()
            parent.replace(script_tag, new_span)
        except Exception as e:
            # Delete this script tag
            parent = script_tag.getparent()
            parent.remove(script_tag)
    
    for tex_attr in ["tex", "data-tex", "data-formula"]:
        for tex_attr_tag in tree.xpath(f'//*[@{tex_attr}]'):
            try:
                text = tex_attr_tag.get(tex_attr)
                if text is None:
                    continue
                text = html_unescape(unquote(text))
                new_span = ET.Element("span", attrib=None, nsmap=None)
                wrapped_text = wrap_math(text)
                new_span.text = wrapped_text
                parent = tex_attr_tag.getparent()
                parent.replace(tex_attr_tag, new_span)
            except Exception as e:
                pass
    
    for tex_attr in ["mathml", "data-mathml"]:
        math_xpath = XPath(f"//*[@{tex_attr}]")
        for math_node in math_xpath(tree):
            try:
                mathml = math_node.get(tex_attr)
                # If this includes xmlns:mml, then we need to replace all
                # instances of mml: with nothing
                if "xmlns:mml" in mathml:
                    mathml = mathml.replace("mml:", "")
                    # replace xmlns:mml="..." with nothing
                    mathml = re.sub(r'xmlns:mml=".*?"', "", mathml)
                latex = mml_to_latex(mathml)
                # replace the node's text
                new_span = ET.Element("span", attrib=None, nsmap=None)
                new_span.text = wrap_math(latex)
                parent = math_node.getparent()
                parent.replace(math_node, new_span)
            except:
                parent = math_node.getparent()
                parent.remove(math_node)
                
    for katex_span in tree.xpath('.//span[contains(@class, "tex")]'):
        try:
            # Check if they have data-expr attr
            expr = katex_span.get("data-expr")
            if expr is None:
                continue
            # Replace with a span
            new_span = ET.Element("span", attrib=None, nsmap=None)
            wrapped_expr = wrap_math(expr)
            new_span.text = wrapped_expr
            parent = katex_span.getparent()
            parent.replace(katex_span, new_span)
        except Exception as e:
            pass
        
    for katex_span in tree.xpath('.//span[contains(@class, "katex")]'):
        katex_html_spans = katex_span.xpath('./span[contains(@class, "katex-html")]')
        for katex_html_span in katex_html_spans:
            parent = katex_html_span.getparent()
            parent.remove(katex_html_span)

    for mathjax_preview_span in tree.xpath('.//span[contains(@class, "MathJax_Preview")]'):
        parent = mathjax_preview_span.getparent()
        parent.remove(mathjax_preview_span)
        
    # Find any math tags, for each math tag, see if there is an annotation tag with
    # encoding="application/x-tex" inside it
    for math_tag in tree.xpath('//math'):
        annotation_tag = math_tag.xpath('annotation[@encoding="application/x-tex"]')
        if annotation_tag:
            # Get the text content of the annotation tag
            text = annotation_tag[0].text
            # Set the content of the math tag to the text
            # replace this math tag with a span tag with the text
            # To do this, we need to get the parent of the math tag
            parent = math_tag.getparent()
            # Then, we need to create a new span tag
            new_span = ET.Element("span", attrib=None, nsmap=None)
            # Set the html of the new span tag to the text
            wrapped_text = wrap_math(text)
            new_span.text = wrapped_text
            # Then, we need to replace the math tag with the new span tag
            parent.replace(math_tag, new_span)
            # If the parent has style="display:none", then we need to
            # remove the style attribute
            style_value = parent.get("style")
            if style_value is not None:
                normalized_style_value = style_value.lower().strip().replace(" ", "").replace(";", "")
                if "display:none" in normalized_style_value:
                    parent.attrib.pop("style", None)
            
        # Check if the math tag has an alttext attribute
        elif "alttext" in math_tag.attrib or "data-code" in math_tag.attrib:
            # Get the alttext attribute
            alttext = math_tag.get("alttext") if "alttext" in math_tag.attrib else math_tag.get("data-code")
            alttext = html_unescape(unquote(alttext))
            new_span = ET.Element("span", attrib=None, nsmap=None)
            # Set the html of the new span tag to the text
            if "data-math-language" in math_tag.attrib:
                if math_tag.get("data-math-language") == "asciimath":
                    wrapped_alttext = wrap_math(extract_asciimath(alttext))
                elif math_tag.get("data-math-language") == "mathml":
                    try:
                        wrapped_alttext = wrap_math(mml_to_latex(alttext))
                    except:
                        wrapped_alttext = wrap_math(alttext)
                else:
                    wrapped_alttext = wrap_math(alttext)
            else:
                wrapped_alttext = wrap_math(alttext)
            new_span.text = wrapped_alttext
            # Then, we need to replace the math tag with the new span tag
            parent = math_tag.getparent()
            parent.replace(math_tag, new_span)
            
        # Otherwise, translate the math tag to LaTeX
        else:
            try:
                # Try translating to LaTeX
                mathml = math_tag.text
                # If this includes xmlns:mml, then we need to replace all
                # instances of mml: with nothing
                if "xmlns:mml" in mathml:
                    mathml = mathml.replace("mml:", "")
                    # replace xmlns:mml="..." with nothing
                    mathml = re.sub(r'xmlns:mml=".*?"', "", mathml)
                latex = mml_to_latex(mathml)
                # Make a new span tag
                new_span = ET.Element("span", attrib=None, nsmap=None)
                # Set the html of the new span tag to the text
                wrapped_latex = wrap_math(latex)
                new_span.text = wrapped_latex
                # Then, we need to replace the math tag with the new span tag
                parent = math_tag.getparent()
                parent.replace(math_tag, new_span)
            except Exception as e:
                parent = math_tag.getparent()
                parent.remove(math_tag)

    for mathjax_tag in tree.xpath('//mathjax'):
        # Get the inner text of the mathjax tag
        text = mathjax_tag.text
        text = html_unescape(text)
        # Use regex to find text wrapped in hashes
        matches = re.findall(r"#(.+?)#", text)
        # For each match, replace the match with the LaTeX
        for match in matches:
            try:
                latex = extract_asciimath(match)
                # Replace the match with the LaTeX
                text = text.replace(f"#{match}#", latex)
            except Exception as e:
                pass

        # Create a new span tag
        new_span = ET.Element("span", attrib=None, nsmap=None)
        # Set the html of the new span tag to the text
        new_span.text = text
        # Then, we need to replace the mathjax tag with the new span tag
        parent = mathjax_tag.getparent()
        parent.replace(mathjax_tag, new_span)
        
    return tree