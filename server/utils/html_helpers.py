from decimal import Decimal

from utils import lc_helper


class Url:
    def __init__(self, href, text=None):
        self.href = href
        self.text = text or href

    def as_html(self):
        return '<a href="{}">{}</a>'.format(self.href, self.text)


class TableCell:
    def __init__(self, value, info=[], prefix="", postfix="", **kwargs):
        self.value = value
        self.info = info
        self.attributes = kwargs
        self.prefix = prefix
        self.postfix = postfix

    def _format_value(self):
        if isinstance(self.value, Decimal):
            return lc_helper.default_currency(self.value, 0)
        return str(self.value)

    def _sign_tag(self, val):
        return "span" if val == 0 else "b"

    def value_html(self, row_type=None):
        html = self._format_value()
        if self.info:
            html += " ({})".format(
                ", ".join(
                    "<{tag}>{val}</{tag}>".format(
                        tag=self._sign_tag(additional), val=(additional and "{:+}".format(additional) or "0")
                    )
                    for additional in self.info
                )
            )
        html = self.prefix + html + self.postfix
        if row_type == "totals":
            html = "<b>{}</b>".format(html)
        return html

    def _get_attributes(self):
        if not self.attributes:
            return ""
        return " " + " ".join('{}="{}"'.format(key, val) for key, val in self.attributes.items())

    def as_html(self, position=1, row_type=None):
        tag = "th" if position == 0 else "td"
        return "<{tag}{attrs}>{val}</{tag}>".format(
            tag=tag, val=self.value_html(row_type), attrs=self._get_attributes()
        )


class TableRow(list):
    TYPE_BREAKDOWN = "breakdown"
    TYPE_TOTALS = "totals"

    def __init__(self, cols, row_type=None):
        super(TableRow, self).__init__(cols)
        self.row_type = row_type

    def as_html(self, position=1):
        html = "<tr>".format(self.row_type)
        for cell in self:
            html += cell.as_html(position, row_type=self.row_type)
        html += "</tr>"
        return html

    @staticmethod
    def prepare(typ):
        return lambda row: TableRow(row, row_type=typ)
