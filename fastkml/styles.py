# Copyright (C) 2012  Christian Ledermann
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA

"""
Once you've created features within Google Earth and examined the KML
code Google Earth generates, you'll notice how styles are an important
part of how your data is displayed.
"""

import logging

from fastkml.base import _BaseObject
from fastkml.config import etree

logger = logging.getLogger(__name__)


class StyleUrl(_BaseObject):
    """
    URL of a <Style> or <StyleMap> defined in a Document. If the style
    is in the same file, use a # reference. If the style is defined in
    an external file, use a full URL along with # referencing.
    """

    __name__ = "styleUrl"
    url = None

    def __init__(self, ns=None, id=None, url=None):
        super().__init__(ns, id)
        self.url = url

    def etree_element(self):
        if self.url:
            element = super().etree_element()
            element.text = self.url
            return element
        else:
            raise ValueError("No url given for styleUrl")

    def from_element(self, element):
        super().from_element(element)
        self.url = element.text


class _StyleSelector(_BaseObject):
    """
    This is an abstract element and cannot be used directly in a KML file.
    It is the base type for the <Style> and <StyleMap> elements. The
    StyleMap element selects a style based on the current mode of the
    Placemark. An element derived from StyleSelector is uniquely identified
    by its id and its url.
    """


class Style(_StyleSelector):
    """
    A Style defines an addressable style group that can be referenced
    by StyleMaps and Features. Styles affect how Geometry is presented
    in the 3D viewer and how Features appear in the Places panel of the
    List view. Shared styles are collected in a <Document> and must have
    an id defined for them so that they can be referenced by the
    individual Features that use them.
    """

    __name__ = "Style"
    _styles = None

    def __init__(self, ns=None, id=None, styles=None):
        super().__init__(ns, id)
        self._styles = []
        if styles:
            for style in styles:
                self.append_style(style)

    def append_style(self, style):
        if isinstance(style, (_ColorStyle, BalloonStyle)):
            self._styles.append(style)
        else:
            raise TypeError

    def styles(self):
        for style in self._styles:
            if isinstance(style, (_ColorStyle, BalloonStyle)):
                yield style
            else:
                raise TypeError

    def from_element(self, element):
        super().from_element(element)
        style = element.find(f"{self.ns}IconStyle")
        if style is not None:
            thestyle = IconStyle(self.ns)
            thestyle.from_element(style)
            self.append_style(thestyle)
        style = element.find(f"{self.ns}LineStyle")
        if style is not None:
            thestyle = LineStyle(self.ns)
            thestyle.from_element(style)
            self.append_style(thestyle)
        style = element.find(f"{self.ns}PolyStyle")
        if style is not None:
            thestyle = PolyStyle(self.ns)
            thestyle.from_element(style)
            self.append_style(thestyle)
        style = element.find(f"{self.ns}LabelStyle")
        if style is not None:
            thestyle = LabelStyle(self.ns)
            thestyle.from_element(style)
            self.append_style(thestyle)
        style = element.find(f"{self.ns}BalloonStyle")
        if style is not None:
            thestyle = BalloonStyle(self.ns)
            thestyle.from_element(style)
            self.append_style(thestyle)

    def etree_element(self):
        element = super().etree_element()
        for style in self.styles():
            element.append(style.etree_element())
        return element


class StyleMap(_StyleSelector):
    """
    A <StyleMap> maps between two different Styles. Typically a
    <StyleMap> element is used to provide separate normal and highlighted
    styles for a placemark, so that the highlighted version appears when
    the user mouses over the icon in Google Earth.
    """

    __name__ = "StyleMap"
    normal = None
    highlight = None

    def __init__(self, ns=None, id=None, normal=None, highlight=None):
        super().__init__(ns, id)
        self.normal = normal
        self.highlight = highlight

    def from_element(self, element):
        super().from_element(element)
        pairs = element.findall(f"{self.ns}Pair")
        for pair in pairs:
            key = pair.find(f"{self.ns}key")
            style = pair.find(f"{self.ns}Style")
            style_url = pair.find(f"{self.ns}styleUrl")
            if key.text == "highlight":
                if style is not None:
                    highlight = Style(self.ns)
                    highlight.from_element(style)
                elif style_url is not None:
                    highlight = StyleUrl(self.ns)
                    highlight.from_element(style_url)
                else:
                    raise ValueError
                self.highlight = highlight
            elif key.text == "normal":
                if style is not None:
                    normal = Style(self.ns)
                    normal.from_element(style)
                elif style_url is not None:
                    normal = StyleUrl(self.ns)
                    normal.from_element(style_url)
                else:
                    raise ValueError
                self.normal = normal
            else:
                raise ValueError

    def etree_element(self):
        element = super().etree_element()
        if self.normal and isinstance(self.normal, (Style, StyleUrl)):
            pair = etree.SubElement(element, f"{self.ns}Pair")
            key = etree.SubElement(pair, f"{self.ns}key")
            key.text = "normal"
            pair.append(self.normal.etree_element())
        if self.highlight and isinstance(self.highlight, (Style, StyleUrl)):
            pair = etree.SubElement(element, f"{self.ns}Pair")
            key = etree.SubElement(pair, f"{self.ns}key")
            key.text = "highlight"
            pair.append(self.highlight.etree_element())
        return element


class _ColorStyle(_BaseObject):
    """
    abstract element; do not create.
    This is an abstract element and cannot be used directly in a KML file.
    It provides elements for specifying the color and color mode of
    extended style types.
    subclasses are: IconStyle, LabelStyle, LineStyle, PolyStyle
    """

    id = None
    ns = None
    color = None
    # Color and opacity (alpha) values are expressed in hexadecimal notation.
    # The range of values for any one color is 0 to 255 (00 to ff).
    # For alpha, 00 is fully transparent and ff is fully opaque.
    # The order of expression is aabbggrr, where aa=alpha (00 to ff);
    # bb=blue (00 to ff); gg=green (00 to ff); rr=red (00 to ff).

    colorMode = None
    # Values for <colorMode> are normal (no effect) and random.
    # A value of random applies a random linear scale to the base <color>

    def __init__(self, ns=None, id=None, color=None, colorMode=None):
        super().__init__(ns, id)
        self.color = color
        self.colorMode = colorMode

    def etree_element(self):
        element = super().etree_element()
        if self.color:
            color = etree.SubElement(element, f"{self.ns}color")
            color.text = self.color
        if self.colorMode:
            colorMode = etree.SubElement(element, f"{self.ns}colorMode")
            colorMode.text = self.colorMode
        return element

    def from_element(self, element):

        super().from_element(element)
        colorMode = element.find(f"{self.ns}colorMode")
        if colorMode is not None:
            self.colorMode = colorMode.text
        color = element.find(f"{self.ns}color")
        if color is not None:
            self.color = color.text


class IconStyle(_ColorStyle):
    """Specifies how icons for point Placemarks are drawn"""

    __name__ = "IconStyle"
    scale = 1.0
    # Resizes the icon. (float)
    heading = None
    # Direction (that is, North, South, East, West), in degrees.
    # Default=0 (North).
    icon_href = None
    # An HTTP address or a local file specification used to load an icon.

    def __init__(
        self,
        ns=None,
        id=None,
        color=None,
        colorMode=None,
        scale=1.0,
        heading=None,
        icon_href=None,
    ):
        super().__init__(ns, id, color, colorMode)
        self.scale = scale
        self.heading = heading
        self.icon_href = icon_href

    def etree_element(self):
        element = super().etree_element()
        if self.scale is not None:
            scale = etree.SubElement(element, f"{self.ns}scale")
            scale.text = str(self.scale)
        if self.heading:
            heading = etree.SubElement(element, f"{self.ns}heading")
            heading.text = str(self.heading)
        if self.icon_href:
            icon = etree.SubElement(element, f"{self.ns}Icon")
            href = etree.SubElement(icon, f"{self.ns}href")
            href.text = self.icon_href
        return element

    def from_element(self, element):
        super().from_element(element)
        scale = element.find(f"{self.ns}scale")
        if scale is not None:
            self.scale = float(scale.text)
        heading = element.find(f"{self.ns}heading")
        if heading is not None:
            self.heading = float(heading.text)
        icon = element.find(f"{self.ns}Icon")
        if icon is not None:
            href = icon.find(f"{self.ns}href")
            if href is not None:
                self.icon_href = href.text


class LineStyle(_ColorStyle):
    """
    Specifies the drawing style (color, color mode, and line width)
    for all line geometry. Line geometry includes the outlines of
    outlined polygons and the extruded "tether" of Placemark icons
    (if extrusion is enabled).
    """

    __name__ = "LineStyle"
    width = 1.0
    # Width of the line, in pixels.

    def __init__(self, ns=None, id=None, color=None, colorMode=None, width=1):
        super().__init__(ns, id, color, colorMode)
        self.width = width

    def etree_element(self):
        element = super().etree_element()
        if self.width is not None:
            width = etree.SubElement(element, f"{self.ns}width")
            width.text = str(self.width)
        return element

    def from_element(self, element):
        super().from_element(element)
        width = element.find(f"{self.ns}width")
        if width is not None:
            self.width = float(width.text)


class PolyStyle(_ColorStyle):
    """
    Specifies the drawing style for all polygons, including polygon
    extrusions (which look like the walls of buildings) and line
    extrusions (which look like solid fences).
    """

    __name__ = "PolyStyle"
    fill = 1
    # Boolean value. Specifies whether to fill the polygon.
    outline = 1
    # Boolean value. Specifies whether to outline the polygon.
    # Polygon outlines use the current LineStyle.

    def __init__(self, ns=None, id=None, color=None, colorMode=None, fill=1, outline=1):
        super().__init__(ns, id, color, colorMode)
        self.fill = fill
        self.outline = outline

    def etree_element(self):
        element = super().etree_element()
        if self.fill is not None:
            fill = etree.SubElement(element, f"{self.ns}fill")
            fill.text = str(self.fill)
        if self.outline is not None:
            outline = etree.SubElement(element, f"{self.ns}outline")
            outline.text = str(self.outline)
        return element

    def from_element(self, element):
        super().from_element(element)
        fill = element.find(f"{self.ns}fill")
        if fill is not None:
            self.fill = int(float(fill.text))
        outline = element.find(f"{self.ns}outline")
        if outline is not None:
            self.outline = int(float(outline.text))


class LabelStyle(_ColorStyle):
    """
    Specifies how the <name> of a Feature is drawn in the 3D viewer
    """

    __name__ = "LabelStyle"
    scale = 1.0
    # Resizes the label.

    def __init__(self, ns=None, id=None, color=None, colorMode=None, scale=1.0):
        super().__init__(ns, id, color, colorMode)
        self.scale = scale

    def etree_element(self):
        element = super().etree_element()
        if self.scale is not None:
            scale = etree.SubElement(element, f"{self.ns}scale")
            scale.text = str(self.scale)
        return element

    def from_element(self, element):
        super().from_element(element)
        scale = element.find(f"{self.ns}scale")
        if scale is not None:
            self.scale = float(scale.text)


class BalloonStyle(_BaseObject):
    """Specifies how the description balloon for placemarks is drawn.
    The <bgColor>, if specified, is used as the background color of
    the balloon."""

    __name__ = "BalloonStyle"

    bgColor = None
    # Background color of the balloon (optional). Color and opacity (alpha)
    # values are expressed in hexadecimal notation. The range of values for
    # any one color is 0 to 255 (00 to ff). The order of expression is
    # aabbggrr, where aa=alpha (00 to ff); bb=blue (00 to ff);
    # gg=green (00 to ff); rr=red (00 to ff).
    # For alpha, 00 is fully transparent and ff is fully opaque.
    # For example, if you want to apply a blue color with 50 percent
    # opacity to an overlay, you would specify the following:
    # <bgColor>7fff0000</bgColor>, where alpha=0x7f, blue=0xff, green=0x00,
    # and red=0x00. The default is opaque white (ffffffff).
    # Note: The use of the <color> element within <BalloonStyle> has been
    # deprecated. Use <bgColor> instead.

    textColor = None
    # Foreground color for text. The default is black (ff000000).

    text = None
    # Text displayed in the balloon. If no text is specified, Google Earth
    # draws the default balloon (with the Feature <name> in boldface,
    # the Feature <description>, links for driving directions, a white
    # background, and a tail that is attached to the point coordinates of
    # the Feature, if specified).
    # You can add entities to the <text> tag using the following format to
    # refer to a child element of Feature: $[name], $[description], $[address],
    # $[id], $[Snippet]. Google Earth looks in the current Feature for the
    # corresponding string entity and substitutes that information in the
    # balloon.
    # To include To here - From here driving directions in the balloon,
    # use the $[geDirections] tag. To prevent the driving directions links
    # from appearing in a balloon, include the <text> element with some content
    # or with $[description] to substitute the basic Feature <description>.
    # For example, in the following KML excerpt, $[name] and $[description]
    # fields will be replaced by the <name> and <description> fields found
    # in the Feature elements that use this BalloonStyle:
    # <text>This is $[name], whose description is:<br/>$[description]</text>

    displayMode = None
    # If <displayMode> is default, Google Earth uses the information supplied
    # in <text> to create a balloon . If <displayMode> is hide, Google Earth
    # does not display the balloon. In Google Earth, clicking the List View
    # icon for a Placemark whose balloon's <displayMode> is hide causes
    # Google Earth to fly to the Placemark.

    def __init__(
        self,
        ns=None,
        id=None,
        bgColor=None,
        textColor=None,
        text=None,
        displayMode=None,
    ):
        super().__init__(ns, id)
        self.bgColor = bgColor
        self.textColor = textColor
        self.text = text
        self.displayMode = displayMode

    def from_element(self, element):
        super().from_element(element)
        bgColor = element.find(f"{self.ns}bgColor")
        if bgColor is not None:
            self.bgColor = bgColor.text
        else:
            bgColor = element.find(f"{self.ns}color")
            if bgColor is not None:
                self.bgColor = bgColor.text
        textColor = element.find(f"{self.ns}textColor")
        if textColor is not None:
            self.textColor = textColor.text
        text = element.find(f"{self.ns}text")
        if text is not None:
            self.text = text.text
        displayMode = element.find(f"{self.ns}displayMode")
        if displayMode is not None:
            self.displayMode = displayMode.text

    def etree_element(self):
        element = super().etree_element()
        if self.bgColor is not None:
            elem = etree.SubElement(element, f"{self.ns}bgColor")
            elem.text = self.bgColor
        if self.textColor is not None:
            elem = etree.SubElement(element, f"{self.ns}textColor")
            elem.text = self.textColor
        if self.text is not None:
            elem = etree.SubElement(element, f"{self.ns}text")
            elem.text = self.text
        if self.displayMode is not None:
            elem = etree.SubElement(element, f"{self.ns}displayMode")
            elem.text = self.displayMode
        return element


__all__ = [
    "BalloonStyle",
    "IconStyle",
    "LabelStyle",
    "LineStyle",
    "PolyStyle",
    "Style",
    "StyleMap",
    "StyleUrl",
]
