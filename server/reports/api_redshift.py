from reports import api_contentads

# TODO: We might want to move api_contentads here
def query(start_date, end_date, breakdown=None, constraints={}):
    return api_contentads.query(start_date, end_date, breakdown=breakdown, constraints=constraints)
