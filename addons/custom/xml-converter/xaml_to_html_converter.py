import html
import xml.etree.ElementTree as ET


def convert_kalizcor_xaml_to_html(xaml_str):
    # #154 — שדות XAML ריקים קיימים בקבצי קלזכור אמיתיים; הם צריכים להפוך לשדה ריק ולא להפיל את הייבוא.
    xaml = html.unescape(xaml_str or "").strip()
    if not xaml:
        return ""
    try:
        tree = ET.ElementTree(ET.fromstring(xaml.replace('<TextDecoration Location="Underline" />', "")))
    except ET.ParseError:
        return html.escape(xaml_str or "", quote=False).strip().replace("\n", "<br>")
    root = tree.getroot()

    for d in root.iter("{http://schemas.microsoft.com/winfx/2006/xaml/presentation}Paragraph"):
        attr = d.attrib
        d.tag = "div"
        html_style = ""
        if (cur_attr := 'TextAlignment') in attr:
            if attr.get(cur_attr) == "Left":
                html_style += "text-align: right;"
            if attr.get(cur_attr) == "Center":
                html_style += "text-align: center;"
            if attr.get(cur_attr) == "Right":
                html_style += "text-align: left;"

        if (cur_attr := 'Margin') in attr:
            d.text = d.text or ""
            d.text = r'&nbsp;' * (int(attr.get(cur_attr).split(",")[0]) // 5) + d.text

        if attr.get('{http://www.w3.org/XML/1998/namespace}space'):
            if html_style == "":
                d.tag = "br"
                d.attrib = {}
            else:
                if d.text is not None:
                    d.text += "<br>"
                else:
                    d.text = "<br>"

        if html_style != "":
            d.attrib = {'style': f"{html_style}"}
        else:
            d.attrib = {}

    for us in root.iter("{http://schemas.microsoft.com/winfx/2006/xaml/presentation}Run.TextDecorations"):
        us.tag = "e"
        sub: ET.Element = ET.SubElement(us, "u")
        sub.text = us.tail
        us.tail = ""

    for u in root.iter("{http://schemas.microsoft.com/winfx/2006/xaml/presentation}TextDecoration"):
        u.tag = "e"
        u.attrib = {}

    for s in root.iter("{http://schemas.microsoft.com/winfx/2006/xaml/presentation}Run"):
        s.tag = "span"
        attr = s.attrib
        html_style = ""
        if (cur_attr := 'FontSize') in attr:
            html_style += f"font-size: {attr.get(cur_attr)}pt; "
        if (cur_attr := 'FontFamily') in attr:
            html_style += f"font-family: {attr.get(cur_attr)}; "
        if (cur_attr := 'Background') in attr and attr.get(cur_attr) != "#00FFFFFF":
            html_style += f"background-color: {attr.get(cur_attr).replace('#FF', '#')}; "

        if (cur_attr := 'Foreground') in attr and attr.get(cur_attr) != "#00FFFFFF":
            html_style += f"color: {attr.get(cur_attr).replace('#FF', '#')}; "

        if 'FontWeight' in attr:
            sub = ET.Element("b")
            sub.text = s.text
            s.text = ""
            for existing_subelement in list(s):
                sub.append(existing_subelement)
                s.remove(existing_subelement)
            s.append(sub)

        if 'FontStyle' in attr:
            sub = ET.Element("i")
            sub.text = s.text
            s.text = ""
            for existing_subelement in list(s):
                sub.append(existing_subelement)
                s.remove(existing_subelement)
            s.append(sub)

        if html_style != "":
            s.attrib = {'style': f"{html_style}"}
        else:
            s.attrib = {}

    for list_ in root.iter("{http://schemas.microsoft.com/winfx/2006/xaml/presentation}List"):
        attr = list_.attrib
        if (cur_attr := 'MarkerStyle') in attr:
            if attr.get(cur_attr) == "Decimal":
                list_.tag = "ol"
                list_.attrib.pop(cur_attr)
            elif attr.get(cur_attr) == "Disc":
                list_.tag = "ul"
                list_.attrib.pop(cur_attr)

    for li in root.iter("{http://schemas.microsoft.com/winfx/2006/xaml/presentation}ListItem"):
        li.tag = "li"
        li.attrib = {}

    for t in root.iter("{clr-namespace:מסמך;assembly=לא_אשכח}מבואר"):
        tt = t.find("span")
        if tt is not None:
            ttse = ET.Element("span")
            ttse.attrib = {'style': "color: #ff3a00;"}
            ttse.text = tt.text
            t.append(ttse)
            t.remove(tt)
        tse = ET.Element("span")
        tse.attrib = {'style': "background-color: rgb(255, 255, 127); color: rgb(170, 168, 160);"}
        tse.text = f"({t.attrib.get('ביאור')})"
        t.append(tse)
        t.tag = "span"
        t.attrib = {}

    root.tag = "e"
    root.attrib = {}
    html_str = (ET.tostring(root, "unicode")
                .replace(" />", ">")
                .replace("&amp;nbsp;", "&nbsp;")
                .replace("&lt;br&gt;", "<br>")
                .replace("<e>", "")
                .replace("</e>", "")
                .replace('<e xmlns:ns0="clr-namespace:מסמך;assembly=לא_אשכח">', "")
                )
    return html_str
