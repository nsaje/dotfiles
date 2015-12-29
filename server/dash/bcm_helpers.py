from django.db import connection, transaction

@transaction.atomic
def delete_credit(credit):
    """
    Completely delete credit from z1.
    The operation is not allowed via models.
    """
    for budget in credit.budgets.all():
        _delete_budget_traces(budget)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM dash_credithistory WHERE credit_id = %s;", [credit.pk])
    cursor.execute("DELETE FROM dash_creditlineitem WHERE id = %s;", [credit.pk])

@transaction.atomic
def delete_budget(budget):
    """
    Completely delete budget from z1.
    The operation is not allowed via models.
    """
    _delete_budget_traces(budget)

def _delete_budget_traces(budget):
    cursor = connection.cursor()
    cursor.execute("DELETE FROM dash_budgethistory WHERE budget_id = %s;", [budget.pk])
    cursor.execute("DELETE FROM reports_budgetdailystatement WHERE budget_id = %s;", [budget.pk])
    cursor.execute("DELETE FROM dash_budgetlineitem WHERE id = %s;", [budget.pk])
    
