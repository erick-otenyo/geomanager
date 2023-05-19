from wagtail.admin.panels import FieldPanel


class ReadOnlyFieldPanel(FieldPanel):
    class BoundPanel(FieldPanel.BoundPanel):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            # swap html disabled --> readonly
            self.bound_field.field.disabled = True
            self.bound_field.field.widget.attrs['readonly'] = True
