import tagulous


class EntityTag(tagulous.models.TagTreeModel):
    class Meta:
        app_label = "dash"
        ordering = ("name",)
