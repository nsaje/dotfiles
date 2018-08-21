from django.forms.widgets import MultiWidget, TextInput, NumberInput, CheckboxInput


class CustomFlagsWidget(MultiWidget):
    template_name = "custom_flags_widgets.html"

    def __init__(self, input_data, attrs=None):
        self.input_data = input_data
        widgets = self._set_widgets(self.input_data)
        super(CustomFlagsWidget, self).__init__(widgets, attrs)

    def _set_widgets(self, data):
        widgets_type = {"string": TextInput, "int": NumberInput, "float": NumberInput, "boolean": CheckboxInput}

        widgets_list = []
        for item in data:
            if item.type in widgets_type.keys():
                widget_instance = widgets_type[item.type](
                    attrs={
                        "id": item.id,
                        "name": item.name,
                        "placeholder": item.type,
                        "title": item.description or "",
                        "advanced": item.advanced,
                    }
                )
                if item.type == "float":
                    widget_instance.attrs.update({"step": 0.1})
                widgets_list.append(widget_instance)
        return widgets_list

    def decompress(self, value):
        if value:
            return [value.get(item.id) for item in self.input_data]
        else:
            return [None for i in range(len(self.widgets))]

    def value_from_datadict(self, data, files, name):
        output = [widget.value_from_datadict(data, files, name + "_%s" % i) for i, widget in enumerate(self.widgets)]
        return output
