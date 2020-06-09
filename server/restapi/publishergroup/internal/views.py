import rest_framework.response
import rest_framework.status
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from rest_framework import permissions

import core.features.publisher_groups
import dash.models
import utils.exc
import zemauth.access
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission

from . import serializers


class PublisherGroupViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request):
        query_params = serializers.PublisherGroupQueryParamsExpectations(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        agency_id = query_params.validated_data.get("agency_id")
        account_id = query_params.validated_data.get("account_id")
        implicit = query_params.validated_data.get("implicit")

        publisher_groups_items = core.features.publisher_groups.PublisherGroup.objects.order_by(
            "-created_dt", "name"
        ).annotate_entities_count()

        if account_id is not None:
            account = zemauth.access.get_account(request.user, Permission.READ, account_id)
            publisher_groups_items = publisher_groups_items.filter_by_account(account)

        elif agency_id is not None:
            agency = zemauth.access.get_agency(request.user, Permission.READ, agency_id)
            publisher_groups_items = publisher_groups_items.filter(Q(agency=agency) | Q(account__agency=agency))

        else:
            raise utils.exc.ValidationError("Either agency id or account id must be provided.")

        if implicit is not None:
            publisher_groups_items = publisher_groups_items.filter_by_implicit(implicit)

        keyword = query_params.validated_data.get("keyword")
        if keyword is not None:
            publisher_groups_items = publisher_groups_items.search(search_expression=keyword)

        paginator = StandardPagination()
        paginated_publisher_groups = paginator.paginate_queryset(publisher_groups_items, request)
        return paginator.get_paginated_response(
            serializers.PublisherGroupSerializer(paginated_publisher_groups, many=True).data
        )

    def remove(self, request, publisher_group_id):
        publisher_group = zemauth.access.get_publisher_group(request.user, Permission.WRITE, publisher_group_id)
        publisher_group.delete(request)
        return rest_framework.response.Response(None, status=rest_framework.status.HTTP_204_NO_CONTENT)


class AddToPublisherGroupViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request):
        serializer = serializers.AddToPublisherGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                publisher_group, _ = core.features.publisher_groups.get_or_create_publisher_group(
                    request,
                    serializer.validated_data.get("name"),
                    publisher_group_id=serializer.validated_data.get("id"),
                    agency_id=serializer.validated_data.get("agency_id"),
                    account_id=serializer.validated_data.get("account_id"),
                    default_include_subdomains=serializer.validated_data.get("default_include_subdomains"),
                )
                core.features.publisher_groups.add_publisher_group_entries(
                    request, publisher_group, serializer.validated_data.get("entries")
                )
            serializer = serializers.AddToPublisherGroupSerializer(publisher_group)
            return rest_framework.response.Response(serializer.data, status=rest_framework.status.HTTP_202_ACCEPTED)
        except dash.models.PublisherGroup.DoesNotExist as e:
            raise utils.exc.ValidationError(errors={"id": [str(e)]})
        except dash.models.Agency.DoesNotExist as e:
            raise utils.exc.ValidationError(errors={"agencyId": [str(e)]})
        except dash.models.Account.DoesNotExist as e:
            raise utils.exc.ValidationError(errors={"accountId": [str(e)]})


class PublisherGroupConnectionsViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def list_connections(self, request, publisher_group_id):
        publisher_group = zemauth.access.get_publisher_group(request.user, Permission.READ, publisher_group_id)
        connections = core.features.publisher_groups.get_publisher_group_connections(request.user, publisher_group.id)
        return self.response_ok(serializers.PublisherGroupConnectionSerializer(connections, many=True).data)

    def remove_connection(self, request, publisher_group_id, location, entity_id):
        try:
            publisher_group = zemauth.access.get_publisher_group(request.user, Permission.WRITE, publisher_group_id)
            core.features.publisher_groups.remove_publisher_group_connection(
                request, publisher_group.id, location, entity_id
            )
            return rest_framework.response.Response(None, status=204)
        except utils.exc.MissingDataError:
            raise utils.exc.ValidationError(errors={"publisher_group_id": ["Publisher group does not exist"]})
        except ValueError:
            raise utils.exc.ValidationError(errors={"publisher_group_id": ["Publisher group does not exist"]})
        except core.features.publisher_groups.InvalidConnectionType:
            # Should not happen, since location is already validated in urls
            raise utils.exc.ValidationError(errors={"location": ["Location does not exist"]})
        except ObjectDoesNotExist:
            raise utils.exc.ValidationError(errors={"entity_id": ["Connection does not exist"]})
