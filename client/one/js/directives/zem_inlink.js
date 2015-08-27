
// Heavily based on https://github.com/angular-ui/ui-router/blob/a7d25c6/src/stateDirectives.js
// Lots of code lifted

function parseStateRef(ref, current) {
  var preparsed = ref.match(/^\s*({[^}]*})\s*$/), parsed;
  if (preparsed) ref = current + '(' + preparsed[1] + ')';
  parsed = ref.replace(/\n/g, " ").match(/^([^(]+?)\s*(\((.*)\))?$/);
  if (!parsed || parsed.length !== 4) throw new Error("Invalid state ref '" + ref + "'");
  return { state: parsed[1], paramExpr: parsed[3] || null };
}

function stateContext(el) {
  var stateData = el.parent().inheritedData('$uiView');

  if (stateData && stateData.state && stateData.state.name) {
    return stateData.state;
  }
}

// Create the part of the url that will come after the questionmark
// Take only the selected parameters from the the dict
function filterAndFormatParams(dict) {
    var str = [];
    var transferredParams = ['start_date', 'end_date', 'filtered_sources', 'show_archived'];
    for(var p in dict) {
        if (transferredParams.indexOf(p) > -1) {
            if (dict[p] !== true) {	
                str.push(encodeURIComponent(p) + "=" + encodeURIComponent(dict[p]));
            } else
            {	
                str.push(encodeURIComponent(p));
            }
        }
    }
    return str.join("&");
};            

$StateRefDirective.$inject = ['$state', '$timeout', '$rootScope', '$location'];
function $StateRefDirective($state, $timeout, $rootScope, $location) {
  var allowedOptions = ['location', 'inherit', 'reload'];

  return {
    restrict: 'A',
    link: function(scope, element, attrs) {
      var ref = null;
      var params = null, url = null, base = stateContext(element) || $state.$current;
      var isForm = element[0].nodeName === "FORM";
      var attr = isForm ? "action" : "href", nav = true;

      var options = { relative: base, inherit: true };

      var update = function(incoming) {
     
        ref = parseStateRef(attrs.zemInLink, $state.current.name);
        params = scope.$eval(ref.paramExpr);

        var newHref = $state.href(ref.state, params, options);
        
        if (newHref === null) {
          nav = false;
          return false;
        }

        var paramStr = filterAndFormatParams($location.search());
        if (paramStr) {
            newHref = newHref + "?" + paramStr;
        }

        element[0][attr] = newHref;
      };
      update();

      scope.$watch(function() {return element.attr('zem-in-link'); }, function(newValue){update()});      
      scope.$on('$locationChangeSuccess', function() {update();});

      if (isForm) return;

      element.bind("click", function(e) {
        var button = e.which || e.button;
        if ( !(button > 1 || e.ctrlKey || e.metaKey || e.shiftKey || element.attr('target')) ) {
          // HACK: This is to allow ng-clicks to be processed before the transition is initiated:
          var transition = $timeout(function() {
            $state.go(ref.state, params, options);
          });
          e.preventDefault();

          e.preventDefault = function() {
            $timeout.cancel(transition);
          };
        }
      });
    }
  };
}

angular.module('one')
  .directive('zemInLink', $StateRefDirective);
