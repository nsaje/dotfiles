import dash.constants
import dash.models
import utils.json_helper


def write_global_history(changes_text,
                         user=None,
                         system_user=None,
                         history_type=dash.constants.HistoryType.ACCOUNT,
                         action_type=None
                         ):
    if not changes_text:
        # don't write history in case of no changes
        return None

    return dash.models.History.objects.create(
        created_by=user,
        system_user=system_user,
        changes_text=changes_text or "",
        type=history_type,
        level=dash.constants.HistoryLevel.GLOBAL,
        action_type=action_type
    )
