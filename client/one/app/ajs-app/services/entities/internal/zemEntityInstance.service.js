var commonHelpers = require('../../../../shared/helpers/common.helpers');

angular
    .module('one.services')
    .service('zemEntityInstanceService', function(
        $http,
        $q,
        zemEntityInstanceEndpoint,
        zemPubSubService,
        zemCloneAdGroupService
    ) {
        function EntityInstanceService(entityType) {
            var EVENTS = {
                ON_ENTITY_CREATED: 'zem-entity-created',
                ON_ENTITY_UPDATED: 'zem-entity-updated',
            };

            var pubsub = zemPubSubService.createInstance();

            //
            // Public API
            //
            this.get = get;
            this.create = create;
            this.clone = clone;
            this.update = update;

            this.onEntityCreated = onEntityCreated;
            this.onEntityUpdated = onEntityUpdated;

            //
            // Internal
            //
            function create(entityProperties) {
                var parentId = entityProperties.parent
                    ? entityProperties.parent.id
                    : null;

                var props = angular.copy(entityProperties);
                delete props.type;
                delete props.parent;

                return zemEntityInstanceEndpoint
                    .create(entityType, parentId, props)
                    .then(function(data) {
                        pubsub.notify(EVENTS.ON_ENTITY_CREATED, {
                            entityType: entityType,
                            parentId: parentId,
                            data: data,
                        });
                        return data;
                    });
            }

            function clone(id, data) {
                return zemCloneAdGroupService
                    .clone(id, data)
                    .then(function(data) {
                        if (commonHelpers.isDefined(data)) {
                            pubsub.notify(EVENTS.ON_ENTITY_CREATED, {
                                entityType: entityType,
                                parentId: data.parentId,
                                data: data,
                            });
                        }
                        return data;
                    });
            }

            function get(id) {
                return zemEntityInstanceEndpoint.get(entityType, id);
            }

            function update(id, data) {
                return zemEntityInstanceEndpoint
                    .update(entityType, id, data)
                    .then(function(data) {
                        pubsub.notify(EVENTS.ON_ENTITY_UPDATED, {
                            entityType: entityType,
                            id: id,
                            data: data,
                        });
                        return data;
                    });
            }

            //
            // Listener functionality
            //
            function onEntityCreated(callback) {
                return pubsub.register(EVENTS.ON_ENTITY_CREATED, callback);
            }

            function onEntityUpdated(callback) {
                return pubsub.register(EVENTS.ON_ENTITY_UPDATED, callback);
            }
        }

        return {
            createInstance: function(entityType) {
                return new EntityInstanceService(entityType);
            },
        };
    });
