from rest_framework import serializers

import restapi.serializers.fields


class UserSerializer(serializers.Serializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    email = serializers.EmailField(read_only=True)
    permissions = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()
    sources_markets = serializers.SerializerMethodField()

    def get_permissions(self, user):
        return user.get_all_permissions_with_access_levels()

    def get_sources(self, user):
        return user.get_sspd_sources()

    def get_sources_markets(self, user):
        return user.get_sspd_sources_markets()
