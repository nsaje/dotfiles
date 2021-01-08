# Backend guidelines

## The purpose of this document

This document describes an agreed upon code design of the Z1 backend. It defines how should we structure our code and what is expected of it.

The goal we want to achieve is to make our programming experience better. With it we can reduce the risk of project delays, security and performance bugs. It also gives programmers more confidence and empoweres them to experiment more.

## How to participate

When you have an idea or think something should be thought about put it into the trello board [Z1 - core](https://trello.com/b/xR1QXkdg/eng-z1-core) or prepare a pull request to this document. Use the trello board also to specify tasks with which we will get to the desired organization.

## Concepts

### Apps

An **app** encapsulates a larger independent system or a independent view of some dependent system. Apps consist of **features** and **common** modules.
 
### Features

A feature has its own **contextual boundaries** and exposes a **public interface**. It should do 1 thing and do it well, so the number of publicly exposed functions should ideally be 1.

![Feature](https://docs.google.com/drawings/d/1tHPhaqdRWsLlF9Kc95-ymQUlqiOzUrHKG0Aa83AMTGQ/pub?w=876&amp;h=455)

Features reside within `features` directory. `core/entities` is a special features directory that is dedicated to core entity features. A feature can consists of:

- **model** (or more of them) - pure data models without logics.
- **model managers** - business logics about models. Class, instance and queryset (read) managers, accessed through a model.
- **service** - higher level, non-model related business logics. `service.py` or `service/` module if single file is not enough.
- **constants** - feature specific constants. `constants.py`.
- **exceptions** - feature specific exceptions. `exceptions.py`
- **`__init__.py`** - feature module that exposes public interface to the feature. It should expose managers through models, services and constants in a way that it can be accessed like `from dash.features import history` and used like `history.write('Something')` or `history.History.objects...`.

#### Feature's directory structure

```
app/
  features/
    <feature-name>/
      __init__.py         # expose public interface to the feature, expose public models and functions
      models/
        __init__.py
        adgroupsettings.py  # model
        adgroup.py          # model
      service.py
      exceptions.py
      constants.py
```

### Models 

Models keep only data, no business logic. Specifies fields, their types and relations to other models. We allow simple getters - eg. `get_name_with_id` - that do not fire additional querysets.
They define how managers are applied to the model:

```
class SomeModel(django.db.models.Model, SomeModelInstanceManager):
    name = CharField()
    ...
    objects = AdGroupManager.from_queryset(AdGroupQuerySet)
```

#### Model directory structure

Depending on the size of the model, there are two ways to structure a model, see comments.

```
adgroupsettings.py  # small model with managers and related business logics, public only AdGroupSettings
adgroup/            # big model with managers, public only AdGroup
  __init__.py       # from model import AdGroup  # make it public
  model.py          # model
  manager.py        # model manager
  instance.py       # model instance manager
  queryset.py       # model queryset manager
  validation.py     # model validation, validation business logics
  exceptions.py     # custom exception classes for model validation
```

### Managers

Managers handle all state changing operations. State changing operations should be atomic (if possible) and should do everything to produce consistent model state. 
They should do business logic validation of own properties, and properties of other models related.

3 sorts of managers: **class**, **instance** and **queryset** managers.
  
#### Class manager

Classic django model managers, expose methods that create new model instances. Classic methods:
- `create`, 
- `create_unsafe`: proxy for the classic django `Model.objects.create` method, that we do not control

#### Instance manager

Instance changing operations like `update`, `delete` and other operations that would result in changed instance properties, for example `launch` a campaign. We also define operations that create new instances based on other instances here, such as `copy`.

#### QuerySet manager

A non-state changing manager that provides an interface for database query operations to models. A QuerySet manager as it is defined by django.

They provide common ways of getting model instances, especially if the query is not trivial.

Trivial query: `ContentAd.objects.filter(ad_group=adgroup)`
Non-trivial query that needs a special method: `ContentAd.objects.filter_by_user(user)`

#### Business logic validation

Business logic validation should happen whenever model state change needs to be persisted. It should raise a subclass of `utils.exc.ValidationError`. 

It is then the upstream's responsibility to properly handle the error and return the correct error description to the client.

### Views

A view represents an outside interface to our system. It can be public, when it is used by our partners, or internal when it is used by our internal systems. They are extracted into separate apps such as `restapi` and `k1api`.

Their responsibilities are the following:

- deserialize into standard representation
- check feature permissions
- check object access permissions
- input validation
- call feature or model manager to execute business logics


Defining and executing anything business logic related is not a responsibility of a view. Business logic should be executed via a single call to a service or manager.

#### K1 View

K1 related views. Views that provide data that is needed to sync Z1 with external systems. These views are internal and can change if k1 calls are changed appropriately.

#### RESTAPI View

Represents a particular view to our app - RESTful API. It defines internal and public endpoints of our system. It follows RESTful API design principles, with - to a certain extent - exceptions for internal endpoints (discussed case by case).

Endpoints are versioned:
- `rest/v1/...`: external view url prefix for `v1` version of the API,
- `rest/internal/...`: internal view url prefix.

We expect our external views to be frozen for longer periods of time. Having this in mind we need to design views that make sense and are highly maintanable. These views can change only in the follwing ways:

- they return an additional parameter
- they accept additional parameters

A `restapi` feature has the following building blocks:

- **urls.py** - url paths
- **views.py** - view definition, calling the right serializers, calling business, returning via serializers
- **serializers.py** - deserialization of request inputs, converting to internal values and vice versa, they can be reused between various views. Idealy we would have 1 serializer per model and reuse it whenever we need the concept in some view. A serializer would know how to serialize a model only by passing in the model instance, without any additional parameters.

```
restapi/
  urls.py
  exceptions.py
  authentication.py
  account/
    __init__.py
    urls.py
    serializers.py
    views.py
    views_test.py
  ...
```

## Directory structure

The Z1 backend is composed of several apps.

- `core` - the gist of z1 backend and it represents its core functionality, such as CRUD on ad groups, ads, campaigns, budgets, pixels etc.
- `dash` - holds side functionality, as for example: search input geolocations, realtimestats from 3rd party sources etc.
- `restapi` - RESTful view of our app.
- `k1api` - consistency related view of our app.
- `redshiftapi` - is a redshift querying engine.
- `utils` - inter-app common code. For example string helpers, test helpers etc.
...

```python
core/
  models/         # core application models
    ad_group/         # ad group model
      __init__.py
      model.py
      manager.py
      instance.py
    ad_group_settings/ # ad group settings model
      __init__.py
      model.py
      manager.py
      instance.py
  features/   # core features
    history/        # history feature
      __init__.py
      models/
        history.py
      constants.py
      service.py
    multicurrency/
      __init__.py
      models/
        currency_exchange_rate.py
      constants.py
      service.py
    ...
dash/
  features/
    geolocations/   # non-core feature (core does not depend on it)
      models/
        geolocation.py
      service.py
    realtimestats/
      service.py
restapi/
  ... # view the RESTAPI view chapter
...
```

### Common code

Code that is shared **within an app** is by general rule put into the top level directory of the app. Modules that could be put into such a module would be common exceptions, base view classes, base serializers, base models that are then derived by feature views, serializers or models within the app.

Code shared **accross apps** should be put into separate apps (eg `redshiftapi`) if that is sufficiently large and independent, or into the `utils` common module if the scope of the concept is small.

### Tests

Tests should share the same namespace as the testee [[7]](#r7). This is why we will be putting tests besides the module we are testing in a way that it alphabetically follows the testee name:

Some examples:

```
adgroup.py
adgroup_test.py

serializers/
  adgroup.py
  adgroup_test.py
  
adgroup/
  model.py
  model_test.py
```

## Unit tests
### Readability and maintainability
A test should only confirm the assumptions about one specific action in the functionality that is being tested. Having many small tests as opposed to a big one containing multiple actions and assertions is much clearer to the potential reader as well as easier to maintain.

### Make the intention clear
What is being tested has to be as clear as possible. To improve the readability the tests should contain the minimal possible setup. Only the relevant values should be set/mocked as well as assertions made only about relevant changes. 

### Test the right thing
A test can pass for the wrong reasons. When testing if a change occurred, assert that the initial value (e.g. a default in the mocked object) is different than what is expected as a result. 

### Test at the appropriate abstraction layer
Unit tests are the most efficient when testing small units. Downstream dependencies should be mocked. E.g. when testing a REST view, we test the responsibility of that layer - serialization and error handling. All calls to the business logic should be mocked. However when mocking a dependency we need to make sure that it is itself thoroughly tested.

### Use test cases to your advantage

When adding tests for a feature, use as many `TestCase`s as necessary to cleanly separate the functionalities being tested. Since test cases provide a way to group setup for all tests in the suite, a new one should be created once two or more tests require similar set up (they can of course differ in key details for a specific test). 

### Tests *are* real code
Tests should be written with the same care as the rest of the codebase. They must have descriptive function and variable names, self explainatory code and when refactoring the related code, the tests should be included in that effort.


## Best practices

### Pass objects, not ids

One way to prevent excesive database access functions should receive objects as inputs whenever they need to operate on it. In case only one parameter is really needed then it's enough to pass only that object property.

### Update model parameters through managers

Never write to a model field or call `save()` directly. Always use model methods and manager methods for state changing operations[2].

### Required parameters should be named

When a method or a function receives `*args` or `**kwargs` make sure that the parameters that are required are named and not a part of the mentioned collections.

### 1 model == 1 module

A model is represented by 1 module that shares the name with the model. In case when model and its managers grow in size, consider making a module with several files and breaking up managers into [separate files](#model-directory-structure).

### Feature can be deleted without consequences

If a feature can be deleted without changing others than its adequately separated.

### Pass `request`

Pass `request` to functions that require the knowledge of the current request context.

### Filter by user

Whenever accessing or modifying objects, make sure the current user has object access to all of the entities you touch.

### Make use of keyword-only arguments

When designing an interface for your feature you can make use of python's built in feature to make sure specific arguments are always specified by name when the function is called. For example:

```python
do_something(request, ad_group, True)
```

is ambigous - you can't assume what the bool parameter does without knowing the function's implementation. A better alternative is calling the funtion with the parameter named:

```python
do_something(request, ad_group, k1_ping=True)
```

Requiring this at call time can be done in the function defintion:
```python
def do_something(request, ad_group, *, k1_ping=True):
  pass
```

(Note: this is not needed in the case when you collect all positional arguments using `*args` when it's enforced automatically)

## Using QuerySets effectively

### Make efficient queries, prefetch related objects

When fetching multiple objects, make sure that you use `select_related` or `prefetch_related` in case you will need access to related objects. This way we prevent making additional queries for every loop iteration.

### Define commonly used methods

Whenever a particular filter expression could be separated create a QuerySet manager method.

## Resources

- <a name="r1"></a>[1]: [Django Design Patterns and Best Practices](https://www.dropbox.com/s/030x7yn1wsyanjs/Django%20Design%20Patterns%20and%20Best%20Practices.pdf?dl=0)
- <a name="r2"></a>[2]: [Django models, encapsulation and data integrity](https://www.dabapps.com/blog/django-models-and-encapsulation/)
- <a name="r3"></a>[3]: [Two Scoops of Django: Best Practices for Django](https://www.twoscoopspress.com/products/two-scoops-of-django-1-8)
- <a name="r4"></a>[4]: [Pro Django](http://prodjango.com/)
- <a name="r5"></a>[5]: [Separation of business logic and data access in django (SO)](https://stackoverflow.com/questions/12578908/separation-of-business-logic-and-data-access-in-django)
- <a name="r6"></a>[6]: [RESTful API design - Quick Reference Card](RESTful-API-design-OCTO-Quick-Reference-Card-2.2.pdf)
- <a name="r7"></a>[7]: [Clean Code Cheatsheet](Clean-Code-V2.2.pdf), [Clean Code: A Handbook of Agile Software Craftsmanship](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- <a name="r8"></a>[8]: [OWASP Top Ten](OWASP_Top_10-2017_RC1-English.pdf), [OWASP Top Ten Project](https://www.owasp.org/index.php/Category:OWASP_Top_Ten_Project)
