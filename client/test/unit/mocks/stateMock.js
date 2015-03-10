// https://gist.github.com/wilsonwc/8358542

angular.module('stateMock',[]);
angular.module('stateMock').service('$state', function($q){
    this.expectedTransitions = [];
    this.transitionTo = function(stateName, params){
        if(this.expectedTransitions.length > 0){
            var expectedState = this.expectedTransitions.shift();
            if(expectedState[0] !== stateName){
                throw Error('Expected transition to state name: ' + expectedState[0] + ' but transitioned to ' + stateName);
            }
            if(!angular.equals(expectedState[1], params)) {
                throw Error('Expected transition with params: ' + expectedState[1] + 'but the params where ' + params);
            }
        }else{
            throw Error('No more transitions were expected! Tried to transition to '+ stateName );
        }
        console.log('Mock transition to: ' + stateName);
        var deferred = $q.defer();
        var promise = deferred.promise;
        deferred.resolve();
        return promise;
    }
    this.go = this.transitionTo;
    this.expectTransitionTo = function(stateName, params){
        this.expectedTransitions.push([stateName, params]);
    }


    this.ensureAllTransitionsHappened = function(){
        if(this.expectedTransitions.length > 0){
            throw Error('Not all transitions happened!');
        }
    }
});
