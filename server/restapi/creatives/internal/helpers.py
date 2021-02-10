from utils import dates_helper


def generate_batch_name():
    return dates_helper.local_now().strftime("%m/%d/%Y %I:%M %p")
