from xlwt import XFStyle

style_usd = XFStyle()
style_usd.num_format_str = u'[$$-409]#,##0.00;-[$$-409]#,##0.00'

style_percent = XFStyle()
style_percent.num_format_str = u'0.00%'

style_date = XFStyle()
style_date.num_format_str = u'M/D/YY'
